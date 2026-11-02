"""CPU-only diagnostics of already returned API objects; never model calls."""
import ast
import collections
import hashlib
import json
import re


def object_sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def returned_prompt(obj):
    choice=obj['choices'][0]
    for path, parent in [('response',obj),('choices[0]',choice)]:
        for key in ['prompt','prompt_text']:
            value=parent.get(key)
            if isinstance(value,str) and value:
                return path+'.'+key,value
    return None,None


def observe_response(obj, *, thinkend_token_id=None, eos_token_ids=(),
                     max_completion_tokens=None):
    choice = obj['choices'][0]
    message = choice['message']
    ids = choice.get('token_ids')
    if ids is None:ids = obj.get('token_ids')
    usage = obj.get('usage') or {}
    content = message.get('content');issues=[]
    if not isinstance(ids,list) or not all(type(x) is int for x in ids):
        issues.append('returned-token-ids-missing-or-invalid');ids=[]
    if usage.get('completion_tokens') != len(ids):issues.append('completion-token-count-mismatch')
    prompt_ids=obj.get('prompt_token_ids',choice.get('prompt_token_ids'))
    if not isinstance(prompt_ids,list) or not all(type(x) is int for x in prompt_ids):
        issues.append('prompt-token-ids-missing-or-invalid');prompt_ids=[]
    if usage.get('prompt_tokens') != len(prompt_ids):issues.append('prompt-token-count-mismatch')
    prompt_field,prompt=returned_prompt(obj)
    if prompt is None:issues.append('returned-prompt-text-missing')
    return dict(id=obj.get('id'),finish_reason=choice.get('finish_reason'),stop_reason=choice.get('stop_reason'),
                content_none=content is None,content_empty=isinstance(content,str) and not content.strip(),
                content_nonempty=isinstance(content,str) and bool(content.strip()),
                reasoning_present=bool(message.get('reasoning_content') or message.get('reasoning')),
                token_count=len(ids),prompt_token_count=len(prompt_ids),usage=usage,token_evidence_issues=issues,
                token_ids_SHA256=object_sha(ids),prompt_token_ids_SHA256=object_sha(prompt_ids),
                full_parsed_API_SHA256=object_sha(obj),prompt_field=prompt_field,
                prompt_SHA256=hashlib.sha256(prompt.encode()).hexdigest() if prompt else None,
                final_token=ids[-1] if ids else None,
                thinkend_count=ids.count(thinkend_token_id) if thinkend_token_id is not None else None,
                eos_counts={str(token):ids.count(token) for token in eos_token_ids},
                eos_before_thinkend=(bool(ids and ids[-1] in eos_token_ids and thinkend_token_id not in ids)
                    if thinkend_token_id is not None else None),
                length_at_limit=(choice.get('finish_reason')=='length' and len(ids)==max_completion_tokens
                    if max_completion_tokens is not None else None),
                prompt_present=prompt is not None,
                limitations='Parser None is not a network timeout; EOS observations are not layer/device causal evidence.')


def strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,list):
        for v in value:yield from strings(v)
    elif isinstance(value,dict):
        for v in value.values():yield from strings(v)


def native_prompt_argument(arguments):
    """Return one complete native prompt, decoding only JSON chat envelopes.

    Native lm_eval may serialize its chat message list into arg_0. Decode
    recognized role/content messages rather than matching JSON syntax against a
    rendered prompt. Preserve plain strings and reject ambiguous candidates.
    """
    args=[value for value in strings(arguments) if len(value)>=80]
    if not args:
        raise ValueError('native sample lacks a usable full prompt argument')
    longest=max(map(len,args))
    candidates=set(value for value in args if len(value)==longest)
    if len(candidates)!=1:
        raise ValueError('ambiguous native prompt arguments')
    argument=candidates.pop()
    try:
        decoded=json.loads(argument)
    except (ValueError,TypeError):
        return argument
    if not isinstance(decoded,list) or not decoded:
        return argument
    if not all(isinstance(msg,dict) and msg.get('role') in
               ('system','developer','user','assistant','tool') and
               isinstance(msg.get('content'),str) for msg in decoded):
        return argument
    users=[msg['content'] for msg in decoded if msg['role']=='user']
    # This observer supports the single complete user prompt used by native
    # generative QA. Multi-turn attribution requires an explicit mapping method.
    if len(users)!=1 or len(users[0])<80:
        raise ValueError('ambiguous or incomplete native JSON chat prompt')
    return users[0]


def scan_native_log(path, raw_output=None, sample_records=None, *,
                    thinkend_token_id=None, eos_token_ids=(),
                    max_completion_tokens=None):
    """Freeze full parsed objects and map only through real returned prompt text.

    A native argument prompt may be inside a chat-template wrapper. Binding
    requires the full decoded native user argument to occur in the returned prompt and to
    identify exactly one document; response order never supplies identity.
    """
    rows=[];transport=collections.Counter();unparsed=0;unmapped=[];prompts={};placeholders=set()
    for record in sample_records or []:
        doc=str(record['doc_id'])
        if doc in prompts:
            raise ValueError('duplicate native document: '+doc)
        try:
            prompts[doc]=native_prompt_argument(record['arguments'])
        except ValueError as exc:
            raise ValueError(str(exc)+': '+doc) from exc
        if any('<TIMEOUT>' in s for s in strings(record.get('resps'))):placeholders.add(doc)
    writer=raw_output.open('x',encoding='utf-8') if raw_output else None
    try:
        with path.open(errors='strict') as handle:
            for line_number,line in enumerate(handle,1):
                for label,pattern in {
                    'timeout_exception_lines':r'ReadTimeout|ConnectTimeout|TimeoutError|timed out',
                    'connection_error_lines':r'ConnectionError|Connection refused|ClientConnectorError',
                    'http_error_lines':r'HTTPError|HTTPStatusError|status code [45][0-9]{2}',
                    'nan_or_device_fault_lines':r'illegal memory access|device-side assert|NaN detected',
                }.items():
                    if re.search(pattern,line,re.I):transport[label]+=1
                if 'choices' not in line or 'token_ids' not in line:continue
                positions=[p for p in (line.find("{'id'"),line.find('{"id"')) if p>=0]
                if not positions:unparsed+=1;continue
                candidate=line[min(positions):].strip();obj=None
                try:obj=json.JSONDecoder().raw_decode(candidate)[0]
                except (ValueError,TypeError):
                    try:obj=ast.literal_eval(candidate)
                    except (ValueError,SyntaxError):pass
                if not isinstance(obj,dict) or not obj.get('choices'):unparsed+=1;continue
                row=observe_response(obj,thinkend_token_id=thinkend_token_id,
                    eos_token_ids=eos_token_ids,max_completion_tokens=max_completion_tokens)
                row['line']=line_number
                if writer:writer.write(json.dumps({'native_log_line':line_number,'API':obj},ensure_ascii=False,allow_nan=False)+'\n')
                if sample_records is not None:
                    _,prompt=returned_prompt(obj)
                    matches=[doc for doc,argument in prompts.items() if prompt and argument in prompt]
                    row['matched_doc_ids']=matches
                    if len(matches)!=1:unmapped.append(dict(line=line_number,response_id=row['id'],matches=matches))
                    else:
                        row['doc_id']=matches[0]
                        row['native_argument_SHA256']=hashlib.sha256(prompts[matches[0]].encode()).hexdigest()
                        row['binding']='unique full native prompt argument (JSON chat decoded when present) contained in returned API prompt'
                rows.append(row)
    finally:
        if writer:writer.close()
    ids=[r['id'] for r in rows if r['id']];covered={r['doc_id'] for r in rows if 'doc_id' in r}
    return dict(parsed_objects=len(rows),unique_response_ids=len(set(ids)),duplicate_response_ids=len(ids)-len(set(ids)),
                unparsed_candidate_lines=unparsed,diagnostics=dict(transport),responses=rows,
                full_parsed_objects=str(raw_output) if raw_output else None,
                prompt_doc_binding=dict(mapped_unique_docs=len(covered),unmapped_objects=unmapped,
                    nonplaceholder_docs_without_returned_API=sorted(set(prompts)-covered-placeholders),
                    placeholder_docs_without_returned_API=sorted(placeholders-covered)),
                limitations='Transport log line counts are not HTTP attempt counts. These are complete parsed API objects, not wire. Multiple responses mapped to a doc do not identify which attempt the native parser selected. Missing APIs for TIMEOUT placeholders do not prove a network timeout.')
