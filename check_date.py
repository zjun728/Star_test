from datetime import date

print("2025 年 3 月日历：")
print("="*50)
for i in range(1, 17):
    d = date(2025, 3, i)
    weekday_cn = d.strftime("%A")
    iso_week = d.isocalendar()[1]
    print(f"3/{i:2d} {weekday_cn:9s} (ISO 第{iso_week}周)")
