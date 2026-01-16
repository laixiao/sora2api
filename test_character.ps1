$env:SORA2API_BASE_URL="https://sora2.diluapp.cn"
$env:SORA2API_API_KEY="han1234"
$env:SORA2API_TEST_VERBOSE="1"
python .\test\test_chat_completions_video_stream.py


# curl --version


# {
#   "id": "chatcmpl-1768320189900",
#   "object": "chat.completion.chunk",
#   "created": 1768320189,
#   "model": "sora",
#   "choices": [-+9*/8
#     {
#       "index": 0,
#       "delta": {
#         "content": null,
#         "reasoning_content": "Setting character as public...\n",
#         "tool_calls": null
#       },
#       "finish_reason": null,
#       "native_finish_reason": null
#     }
#   ],
#   "usage": {
#     "prompt_tokens": 0
#   }
# }


# {
#   "success": true,
#   "username": "quackchamp386",
#   "display_name": "Sunny Rally Duck",
#   "character_id": "ch_69666ca2a63c81918e80eaf4ddfe8815",
#   "cameo_id": "69666ca2c39081919af589edb0c796d9"
# }