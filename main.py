import flet as ft
import jdatetime
from flet_android_notifications import FletAndroidNotifications
import json
import os
from datetime import datetime, time

# مسیر ذخیره اطلاعات
DATA_FILE = "birthdays.json"

def load_birthdays():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_birthdays(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main(page: ft.Page):
    page.title = "🎂 یادآور تولد شمسی"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True  # راست‌چین برای فارسی
    page.padding = 20

    # راه‌اندازی سرویس نوتیفیکیشن (فقط یک بار)
    notifications = FletAndroidNotifications()

    # --- بخش نمایش لیست تولدها ---
    birthday_list = ft.Column(spacing=10)

    def refresh_list():
        birthday_list.controls.clear()
        birthdays = load_birthdays()
        if not birthdays:
            birthday_list.controls.append(
                ft.Text("هنوز هیچ تولدی ثبت نشده است.", color="grey")
            )
        else:
            for b in birthdays:
                birthday_list.controls.append(
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.Icons.CAKE, color=ft.Colors.PINK),
                            title=ft.Text(b["name"], weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"{b['day']} / {b['month']} (شمسی)"),
                        ),
                        border_radius=10,
                        bgcolor=ft.Colors.PINK_50,
                    )
                )
        page.update()

    # --- فرم افزودن تولد جدید ---
    name_field = ft.TextField(label="نام شخص", text_align=ft.TextAlign.RIGHT)
    day_field = ft.TextField(label="روز (۱ تا ۳۱)", keyboard_type=ft.KeyboardType.NUMBER, width=120)
    month_field = ft.TextField(label="ماه (۱ تا ۱۲)", keyboard_type=ft.KeyboardType.NUMBER, width=120)

    async def add_birthday(e):
        name = name_field.value.strip()
        try:
            day = int(day_field.value)
            month = int(month_field.value)
            if not (1 <= day <= 31 and 1 <= month <= 12):
                raise ValueError
        except:
            page.snack_bar = ft.SnackBar(ft.Text("لطفاً روز و ماه معتبر وارد کن!"))
            page.snack_bar.open = True
            page.update()
            return

        if not name:
            page.snack_bar = ft.SnackBar(ft.Text("نام را وارد کن!"))
            page.snack_bar.open = True
            page.update()
            return

        # ۱. ذخیره در فایل
        birthdays = load_birthdays()
        birthdays.append({"name": name, "day": day, "month": month})
        save_birthdays(birthdays)

        # ۲. زمان‌بندی نوتیفیکیشن برای امسال (یا سال بعد اگر گذشته باشد)
        today = jdatetime.date.today()
        try:
            target_date = jdatetime.date(today.year, month, day)
        except ValueError: # اگر تاریخ نامعتبر بود (مثلاً ۳۱ اسفند)
            target_date = jdatetime.date(today.year, month, 28) 

        if target_date < today:
            target_date = jdatetime.date(today.year + 1, month, day)

        # درخواست مجوزها (فقط یک بار لازم است)
        await notifications.request_permissions()
        await notifications.request_exact_alarm_permission()

        # زمان‌بندی نوتیفیکیشن (ساعت ۹ صبح روز تولد)
        scheduled_dt = datetime.combine(
            target_date.togregorian(),
            time(9, 0)
        )

        await notifications.schedule_notification(
            notification_id=abs(hash(name)) % 10000,
            title=f"🎂 تولد {name}",
            body=f"امروز تولد {name} است! یادت نره تبریک بگی.",
            scheduled_time=scheduled_dt,
        )

        # ۳. پاک کردن فرم و رفرش لیست
        name_field.value = ""
        day_field.value = ""
        month_field.value = ""
        refresh_list()
        page.snack_bar = ft.SnackBar(ft.Text(f"تولد {name} ذخیره و یادآور تنظیم شد!"))
        page.snack_bar.open = True
        page.update()

    add_button = ft.ElevatedButton(
        "افزودن و تنظیم یادآور",
        icon=ft.Icons.ADD_ALARM,
        on_click=add_birthday,
        style=ft.ButtonStyle(bgcolor=ft.Colors.PINK, color=ft.Colors.WHITE)
    )

    # --- چیدمان صفحه ---
    page.add(
        ft.Text("🎂 یادآور تولد شمسی", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.PINK_700),
        ft.Divider(),
        ft.Text("اطلاعات تولد را وارد کن:", size=16, weight=ft.FontWeight.W_500),
        name_field,
        ft.Row([day_field, month_field], alignment=ft.MainAxisAlignment.START),
        add_button,
        ft.Divider(height=30),
        ft.Text("📋 لیست تولدها:", size=18, weight=ft.FontWeight.BOLD),
        birthday_list,
    )

    refresh_list()

# اجرای برنامه (این خط برای ساخت APK کاملاً درست است)
ft.app(target=main)
