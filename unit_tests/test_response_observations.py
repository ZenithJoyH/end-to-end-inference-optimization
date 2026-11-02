"""CPU tests of exact native prompt attribution; no evaluator or model import."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evaluation/accuracy'))
from response_observations import native_prompt_argument, scan_native_log, observe_response

PROMPT='Question: '+('长输入 "quoted"\nwith \\ and U+2028\u2028. '*8)

def record(doc=0,prompt=PROMPT):
    return dict(doc_id=doc,arguments={'gen_args_0':{'arg_0':[json.dumps([dict(role='user',content=prompt)],ensure_ascii=False)],'arg_1':{'temperature':1}}},resps=[['B']])

def api(prompt=PROMPT,finish='stop',content='B'):
    return dict(id='chat-1',prompt_text='<system>instructions</system><user>'+prompt+'</user>',prompt_token_ids=[1],choices=[dict(message=dict(content=content),finish_reason=finish,token_ids=[248069,248046])],usage=dict(prompt_tokens=1,completion_tokens=2))

class NativeResponseMappingTests(unittest.TestCase):
    def scan(self,obj,records,partial=False):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'native.log';out=Path(folder)/'objects.jsonl'
            p.write_text('INFO API '+(str(obj)[:120] if partial else repr(obj))+'\n')
            result=scan_native_log(p,out,records,thinkend_token_id=248069,
                                   eos_token_ids=(248046,248044),max_completion_tokens=60000)
            if not partial:
                self.assertEqual(json.loads(out.read_text())['API'],obj)
            return result
    def test_generic_observer_does_not_assume_token_vocabulary(self):
        row=observe_response(api())
        self.assertIsNone(row['thinkend_count'])
        self.assertEqual(row['eos_counts'],{})
        self.assertIsNone(row['length_at_limit'])
    def test_explicit_token_vocabulary_and_limit(self):
        obj=api();obj['choices'][0]['token_ids']=[3,4]
        row=observe_response(obj,thinkend_token_id=3,eos_token_ids=(4,5),max_completion_tokens=2)
        self.assertEqual(row['thinkend_count'],1)
        self.assertEqual(row['eos_counts'],{'4':1,'5':0})
        self.assertFalse(row['eos_before_thinkend'])
    def test_serialized_chat_decoded_exactly(self):
        self.assertEqual(native_prompt_argument(record()['arguments']),PROMPT)
        r=self.scan(api(),[record()])
        self.assertEqual(r['responses'][0]['doc_id'],'0')
        self.assertEqual(r['prompt_doc_binding']['unmapped_objects'],[])
        self.assertEqual(r['responses'][0]['token_evidence_issues'],[])
    def test_plain_argument_supported(self):
        r=record();r['arguments']={'arg_0':[PROMPT]}
        self.assertEqual(self.scan(api(),[r])['prompt_doc_binding']['mapped_unique_docs'],1)
    def test_json_that_is_not_chat_stays_literal(self):
        value=json.dumps({'text':PROMPT})
        self.assertEqual(native_prompt_argument([value]),value)
    def test_malformed_json_is_not_unescaped(self):
        value='[{"role":"user","content":'+PROMPT
        self.assertEqual(native_prompt_argument([value]),value)
        r=record();r['arguments']=[value]
        self.assertEqual(len(self.scan(api(),[r])['prompt_doc_binding']['unmapped_objects']),1)
    def test_multiuser_chat_rejected(self):
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            native_prompt_argument([json.dumps([dict(role='user',content=PROMPT),dict(role='user',content=PROMPT)])])
    def test_equal_long_arguments_rejected(self):
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            native_prompt_argument(['a'*100,'b'*100])
    def test_duplicate_doc_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate native document'):
            self.scan(api(),[record(),record()])
    def test_same_prompt_two_docs_cannot_bind(self):
        r=self.scan(api(),[record(0),record(1)])
        self.assertEqual(r['prompt_doc_binding']['mapped_unique_docs'],0)
        self.assertEqual(r['prompt_doc_binding']['unmapped_objects'][0]['matches'],['0','1'])
    def test_none_length_is_not_transport_timeout(self):
        obj=api(finish='length',content=None);obj['choices'][0]['token_ids']=[7]*60000;obj['usage']['completion_tokens']=60000
        r=record();r['resps']=[['<TIMEOUT>']]
        result=self.scan(obj,[r]);row=result['responses'][0]
        self.assertTrue(row['length_at_limit']);self.assertTrue(row['content_none'])
        self.assertEqual(result['diagnostics'],{})
        self.assertEqual(result['prompt_doc_binding']['mapped_unique_docs'],1)
    def test_partial_api_log_counted_invalid(self):
        obj=api();line='INFO '+repr(obj)[:-4]
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'native.log';p.write_text(line+'\n')
            result=scan_native_log(p,sample_records=[record()])
        self.assertEqual(result['parsed_objects'],0)
        self.assertEqual(result['unparsed_candidate_lines'],1)

if __name__=='__main__':unittest.main()
