from datetime import datetime
from zoneinfo import ZoneInfo

utc_now = datetime.now(ZoneInfo("UTC"))
print(f"当前 UTC 时间: {utc_now}")
