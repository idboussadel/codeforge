"""ponytail: cache usage extraction self-check."""
from codeforge.agent.cache import extract_turn_usage, merge_usage


class _FakeUsage:
    input_tokens = 100
    output_tokens = 50


class _FakeOutput:
    usage_metadata = _FakeUsage()
    response_metadata = {
        "token_usage": {
            "prompt_cache_hit_tokens": 80,
            "prompt_cache_miss_tokens": 20,
        }
    }


turn = extract_turn_usage(_FakeOutput())
assert turn["cacheRead"] == 80
assert turn["cacheMiss"] == 20
assert merge_usage({"input": 10, "output": 5, "cacheRead": 1, "cacheMiss": 2}, turn)["cacheRead"] == 81
print("cache self-check passed")
