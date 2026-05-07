with open('app/main.py', 'r') as f:
    lines = f.readlines()

new_lines = lines[:8] + [
    "from slowapi import _rate_limit_exceeded_handler\n",
    "from slowapi.errors import RateLimitExceeded\n",
    "from .utils import limiter\n\n"
] + lines[28:]

with open('app/main.py', 'w') as f:
    f.writelines(new_lines)
