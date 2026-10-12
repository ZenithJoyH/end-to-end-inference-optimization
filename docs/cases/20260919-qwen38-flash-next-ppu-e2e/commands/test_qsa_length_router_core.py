#!/usr/bin/env python3

import unittest

from qsa_length_router_core import BOUND_TOKENS, bounded_is_safe, build_tokenize_payload


class RouterCoreTest(unittest.TestCase):
    def test_completion_payload(self):
        request = {"model": "m", "prompt": "hello", "max_tokens": 4, "temperature": 1}
        self.assertEqual(
            build_tokenize_payload("/v1/completions", request),
            {"model": "m", "prompt": "hello"},
        )

    def test_chat_payload_preserves_template_controls(self):
        request = {
            "model": "m",
            "messages": [{"role": "user", "content": "hello"}],
            "tools": [{"type": "function", "function": {"name": "f"}}],
            "continue_final_message": False,
            "max_tokens": 4,
        }
        result = build_tokenize_payload("/v1/chat/completions", request)
        self.assertEqual(result["messages"], request["messages"])
        self.assertEqual(result["tools"], request["tools"])
        self.assertFalse(result["continue_final_message"])

    def test_ambiguous_inputs_fail_closed(self):
        self.assertIsNone(build_tokenize_payload("/v1/completions", {"prompt": [1, 2]}))
        self.assertIsNone(build_tokenize_payload("/v1/completions", {"prompt": ["a", "b"]}))
        self.assertIsNone(build_tokenize_payload(
            "/v1/chat/completions",
            {"messages": [{"role": "user", "content": [{"type": "text", "text": "x"}]}]},
        ))

    def test_boundary(self):
        payload = {"max_tokens": 1024}
        self.assertEqual(bounded_is_safe(payload, BOUND_TOKENS - 1025)[0], True)
        self.assertEqual(bounded_is_safe(payload, BOUND_TOKENS - 1024)[0], True)
        self.assertEqual(bounded_is_safe(payload, BOUND_TOKENS - 1023)[0], False)

    def test_missing_invalid_or_boolean_max_tokens_fail_closed(self):
        for value in (None, -1, 1.5, True, "1024"):
            payload = {} if value is None else {"max_tokens": value}
            self.assertFalse(bounded_is_safe(payload, 10)[0])

    def test_invalid_prompt_count_fails_closed(self):
        for count in (-1, True, 1.5, None):
            self.assertFalse(bounded_is_safe({"max_tokens": 1}, count)[0])


if __name__ == "__main__":
    unittest.main()
