import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

group_tasks = {}

def get_tasks(chat_id):
    if chat_id not in group_tasks:
        group_tasks[chat_id] = []
    return group_tasks[chat_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Todo + Reminder Bot*\n\n"
        "/addtask - Task add karo\n"
        "/tasks - Tasks dekho\n"
        "/done - Task complete karo\n"
        "/deltask - Task delete karo\n"
        "/remind - Reminder set karo\n"
        "/help - Help dekho",
        parse_mode="Markdown"
    )

async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("❌ Task likho!\nExample: /addtask Math homework")
        return
    task = " ".join(context.args)
    tasks = get_tasks(chat_id)
    tasks.append({"task": task, "done": False})
    await update.message.reply_text(f"✅ Task #{len(tasks)} add hua:\n📝 {task}")

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tasks = get_tasks(chat_id)
    if not tasks:
        await update.message.reply_text("📋 Koi task nahi hai!\n/addtask se add karo")
        return
    msg = "📋 *Todo List:*\n\n"
    for i, t in enumerate(tasks, 1):
        status = "✅" if t["done"] else "⏳"
        msg += f"{status} #{i} {t['task']}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("❌ Task number likho!\nExample: /done 1")
        return
    try:
        num = int(context.args[0]) - 1
        tasks = get_tasks(chat_id)
        if 0 <= num < len(tasks):
            tasks[num]["done"] = True
            await update.message.reply_text(f"🎉 Task #{num+1} complete!\n✅ {tasks[num]['task']}")
        else:
            await update.message.reply_text("❌ Galat number!")
    except:
        await update.message.reply_text("❌ Sirf number likho!")

async def deltask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("❌ Task number likho!\nExample: /deltask 1")
        return
    try:
        num = int(context.args[0]) - 1
        tasks = get_tasks(chat_id)
        if 0 <= num < len(tasks):
            removed = tasks.pop(num)
            await update.message.reply_text(f"🗑️ Task delete hua:\n{removed['task']}")
        else:
            await update.message.reply_text("❌ Galat number!")
    except:
        await update.message.reply_text("❌ Sirf number likho!")

async def cleartasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    group_tasks[chat_id] = []
    await update.message.reply_text("🗑️ Saari tasks delete ho gayi!")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(
        job.chat_id,
        f"🔔 *REMINDER!*\n\n📝 {job.data}",
        parse_mode="Markdown"
    )

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Sahi format:\n/remind 1 30min\n/remind 1 2hour\n/remind 1 1day"
        )
        return
    try:
        num = int(context.args[0]) - 1
        time_str = context.args[1].lower()
        tasks = get_tasks(chat_id)
        if not (0 <= num < len(tasks)):
            await update.message.reply_text("❌ Galat task number!")
            return
        if "min" in time_str:
            seconds = int(time_str.replace("min", "")) * 60
            label = time_str
        elif "hour" in time_str:
            seconds = int(time_str.replace("hour", "")) * 3600
            label = time_str
        elif "day" in time_str:
            seconds = int(time_str.replace("day", "")) * 86400
            label = time_str
        else:
            await update.message.reply_text("❌ 30min, 2hour, ya 1day format use karo!")
            return
        task_name = tasks[num]["task"]
        context.job_queue.run_once(
            send_reminder,
            seconds,
            chat_id=chat_id,
            name=f"{chat_id}_{num}",
            data=task_name
        )
        await update.message.reply_text(
            f"⏰ Reminder set!\n📝 {task_name}\n🕐 {label} baad yaad dilaunga!"
        )
    except:
        await update.message.reply_text("❌ Kuch galat hua, dobara try karo!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Commands:*\n\n"
        "/addtask [task] - Task add karo\n"
        "/tasks - Saari tasks dekho\n"
        "/done [number] - Task complete karo\n"
        "/deltask [number] - Task delete karo\n"
        "/cleartasks - Saari tasks hatao\n"
        "/remind [number] [time] - Reminder set karo\n"
        "  30min, 2hour, 1day format use karo",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addtask", addtask))
    app.add_handler(CommandHandler("tasks", show_tasks))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("deltask", deltask))
    app.add_handler(CommandHandler("cleartasks", cleartasks))
    app.add_handler(CommandHandler("remind", remind))
    app.add_handler(CommandHandler("help", help_cmd))
    print("Bot start ho gaya!")
    app.run_polling()

if __name__ == "__main__":
    main()
