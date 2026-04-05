import os
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import anthropic

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

group_tasks = {}
group_exams = {}
group_notes = {}

def get_tasks(chat_id):
    if chat_id not in group_tasks:
        group_tasks[chat_id] = []
    return group_tasks[chat_id]

def get_exams(chat_id):
    if chat_id not in group_exams:
        group_exams[chat_id] = []
    return group_exams[chat_id]

def get_notes(chat_id):
    if chat_id not in group_notes:
        group_notes[chat_id] = {}
    return group_notes[chat_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Student Helper Bot*\n\n"
        "📚 *Homework:*\n"
        "/addtask [subject] [task]\n"
        "/tasks - Saari tasks\n"
        "/done [number] - Complete\n"
        "/deltask [number] - Delete\n"
        "/priority [number] [high/medium/low]\n"
        "/due [number] [DD-MM]\n"
        "/remind [number] [30min/2hour/1day]\n\n"
        "📝 *Exams:*\n"
        "/addexam [subject] [DD-MM]\n"
        "/exams - List dekho\n\n"
        "📒 *Notes:*\n"
        "/note [subject] [text]\n"
        "/notes [subject]\n\n"
        "⏱️ /studytimer - Pomodoro 25min\n"
        "📊 /progress - Progress dekho\n\n"
        "🤖 *AI Features:*\n"
        "/aisummary [text]\n"
        "/mindmap [topic]\n"
        "Photo bhejo → Auto summary!\n\n"
        "/help - Full help",
        parse_mode="Markdown"
    )

async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text("❌ Format: `/addtask Math Algebra chapter 3`", parse_mode="Markdown")
        return
    subject = context.args[0]
    task = " ".join(context.args[1:])
    tasks = get_tasks(chat_id)
    tasks.append({"task": task, "subject": subject, "done": False, "priority": "medium", "due": None})
    num = len(tasks)
    await update.message.reply_text(
        f"✅ Task #{num} add hua!\n📚 {subject}\n📝 {task}\n🟡 Priority: Medium\n\n"
        f"Tip: `/priority {num} high` ya `/due {num} 25-04`",
        parse_mode="Markdown"
    )

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tasks = get_tasks(chat_id)
    if not tasks:
        await update.message.reply_text("📋 Koi task nahi!\n/addtask se add karo")
        return
    pending = [t for t in tasks if not t["done"]]
    completed = [t for t in tasks if t["done"]]
    msg = f"📋 *Todo List* ({len(pending)} pending, {len(completed)} done)\n\n"
    if pending:
        msg += "⏳ *Pending:*\n"
        for i, t in enumerate(tasks, 1):
            if not t["done"]:
                p = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(t["priority"], "🟡")
                due = f" | 📅 {t['due']}" if t.get("due") else ""
                msg += f"{p} #{i} [{t['subject']}] {t['task']}{due}\n"
    if completed:
        msg += "\n✅ *Completed:*\n"
        for i, t in enumerate(tasks, 1):
            if t["done"]:
                msg += f"✅ #{i} [{t['subject']}] {t['task']}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("❌ Example: `/done 1`", parse_mode="Markdown")
        return
    try:
        num = int(context.args[0]) - 1
        tasks = get_tasks(chat_id)
        if 0 <= num < len(tasks):
            tasks[num]["done"] = True
            await update.message.reply_text(f"🎉 Complete!\n✅ [{tasks[num]['subject']}] {tasks[num]['task']}\nShabaash! 💪")
        else:
            await update.message.reply_text("❌ Galat number!")
    except:
        await update.message.reply_text("❌ Sirf number likho!")

async def deltask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("❌ Example: `/deltask 1`", parse_mode="Markdown")
        return
    try:
        num = int(context.args[0]) - 1
        tasks = get_tasks(chat_id)
        if 0 <= num < len(tasks):
            removed = tasks.pop(num)
            await update.message.reply_text(f"🗑️ Delete hua:\n[{removed['subject']}] {removed['task']}")
        else:
            await update.message.reply_text("❌ Galat number!")
    except:
        await update.message.reply_text("❌ Sirf number likho!")

async def cleartasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_tasks[update.effective_chat.id] = []
    await update.message.reply_text("🗑️ Saari tasks delete!")

async def set_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text("❌ Example: `/priority 1 high`", parse_mode="Markdown")
        return
    try:
        num = int(context.args[0]) - 1
        priority = context.args[1].lower()
        if priority not in ["high", "medium", "low"]:
            await update.message.reply_text("❌ high, medium, ya low likho!")
            return
        tasks = get_tasks(chat_id)
        if 0 <= num < len(tasks):
            tasks[num]["priority"] = priority
            e = {"high": "🔴", "medium": "🟡", "low": "🟢"}[priority]
            await update.message.reply_text(f"{e} Task #{num+1} priority: {priority.upper()}")
        else:
            await update.message.reply_text("❌ Galat number!")
    except:
        await update.message.reply_text("❌ Galat format!")

async def set_due(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text("❌ Example: `/due 1 25-04`", parse_mode="Markdown")
        return
    try:
        num = int(context.args[0]) - 1
        tasks = get_tasks(chat_id)
        if 0 <= num < len(tasks):
            tasks[num]["due"] = context.args[1]
            await update.message.reply_text(f"📅 Task #{num+1} due: {context.args[1]}")
        else:
            await update.message.reply_text("❌ Galat number!")
    except:
        await update.message.reply_text("❌ Galat format!")

async def addexam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text("❌ Format: `/addexam Math 25-04`", parse_mode="Markdown")
        return
    exams = get_exams(chat_id)
    exams.append({"subject": context.args[0], "date": context.args[1]})
    await update.message.reply_text(f"📝 Exam add hua!\n📚 {context.args[0]}\n📅 {context.args[1]}")

async def show_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    exams = get_exams(chat_id)
    if not exams:
        await update.message.reply_text("📝 Koi exam nahi!\n/addexam se add karo")
        return
    msg = "📝 *Upcoming Exams:*\n\n"
    for i, e in enumerate(exams, 1):
        msg += f"📚 #{i} {e['subject']} — 📅 {e['date']}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text("❌ Format: `/note Math Newton laws`", parse_mode="Markdown")
        return
    subject = context.args[0]
    note_text = " ".join(context.args[1:])
    notes = get_notes(chat_id)
    if subject not in notes:
        notes[subject] = []
    notes[subject].append(note_text)
    await update.message.reply_text(f"📒 Note save!\n📚 {subject}\n📝 {note_text}")

async def show_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    notes = get_notes(chat_id)
    if not context.args:
        if not notes:
            await update.message.reply_text("📒 Koi notes nahi!")
            return
        msg = "📒 *Subjects:*\n\n"
        for s in notes:
            msg += f"📚 {s} ({len(notes[s])} notes)\n"
        msg += "\nDekhne ke liye: `/notes Math`"
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    subject = context.args[0]
    if subject not in notes or not notes[subject]:
        await update.message.reply_text(f"📒 {subject} ke notes nahi!")
        return
    msg = f"📒 *{subject} Notes:*\n\n"
    for i, n in enumerate(notes[subject], 1):
        msg += f"{i}. {n}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def timer_done(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        context.job.chat_id,
        "🎉 *25 min complete!*\n\n☕ 5 min break lo!\nPhir /studytimer se next session!",
        parse_mode="Markdown"
    )

async def study_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏱️ *Pomodoro Start!*\n\n📚 25 min study karo!\nPhone mat dekho! 💪", parse_mode="Markdown")
    context.job_queue.run_once(timer_done, 25 * 60, chat_id=chat_id)

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tasks = get_tasks(chat_id)
    if not tasks:
        await update.message.reply_text("📊 Koi task nahi!\n/addtask se add karo")
        return
    total = len(tasks)
    completed = len([t for t in tasks if t["done"]])
    percent = int((completed / total) * 100)
    bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
    high = len([t for t in tasks if not t["done"] and t["priority"] == "high"])
    msg = f"📊 *Progress*\n\n[{bar}] {percent}%\n\n✅ Complete: {completed}/{total}\n🔴 High priority pending: {high}\n\n"
    if percent == 100:
        msg += "🎉 Waah! Sab complete!"
    elif percent >= 50:
        msg += "💪 Achha chal raha hai!"
    else:
        msg += "📚 Mehnat karo! Tu kar sakta hai!"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(context.job.chat_id, f"🔔 *REMINDER!*\n\n📝 {context.job.data}", parse_mode="Markdown")

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text("❌ Format: `/remind 1 30min`", parse_mode="Markdown")
        return
    try:
        num = int(context.args[0]) - 1
        time_str = context.args[1].lower()
        tasks = get_tasks(chat_id)
        if not (0 <= num < len(tasks)):
            await update.message.reply_text("❌ Galat number!")
            return
        if "min" in time_str:
            seconds = int(time_str.replace("min", "")) * 60
        elif "hour" in time_str:
            seconds = int(time_str.replace("hour", "")) * 3600
        elif "day" in time_str:
            seconds = int(time_str.replace("day", "")) * 86400
        else:
            await update.message.reply_text("❌ 30min, 2hour, ya 1day use karo!")
            return
        task_name = f"[{tasks[num]['subject']}] {tasks[num]['task']}"
        context.job_queue.run_once(send_reminder, seconds, chat_id=chat_id, data=task_name)
        await update.message.reply_text(f"⏰ Reminder set!\n📝 {task_name}\n🕐 {time_str} baad!")
    except:
        await update.message.reply_text("❌ Kuch galat hua!")

async def ai_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Format: `/aisummary [text]`", parse_mode="Markdown")
        return
    text = " ".join(context.args)
    await update.message.reply_text("🤖 AI summary bana raha hai...")
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": f"Yeh notes ka simple summary banao Hindi mein. Clear aur short rakho:\n\n{text}"}]
        )
        await update.message.reply_text(f"📝 *AI Summary:*\n\n{msg.content[0].text}", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ AI error! Baad mein try karo.")

async def mind_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Format: `/mindmap [topic]`", parse_mode="Markdown")
        return
    text = " ".join(context.args)
    await update.message.reply_text("🤖 Mind map bana raha hai...")
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": f"Is topic ka mind map banao tree format mein. Hindi mein. Emojis use karo:\n📚 Main Topic\n├── 🔹 Subtopic\n│   └── Detail\n\nTopic: {text}"}]
        )
        await update.message.reply_text(f"🗺️ *Mind Map:*\n\n{msg.content[0].text}", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ AI error! Baad mein try karo.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Photo mili! AI summary bana raha hai... 🤖")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        file_bytes = await file.download_as_bytearray()
        image_data = base64.standard_b64encode(file_bytes).decode("utf-8")
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                    {"type": "text", "text": "Yeh notes ki image hai. Summary banao Hindi mein. Important points highlight karo."}
                ]
            }]
        )
        await update.message.reply_text(
            f"📝 *Notes Summary:*\n\n{msg.content[0].text}\n\nMind map ke liye: `/mindmap [topic]`",
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text("❌ Photo read nahi hui! Clear photo bhejo.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Full Help:*\n\n"
        "📚 *Homework:*\n"
        "`/addtask Math Algebra ch3`\n"
        "`/tasks` `/done 1` `/deltask 1`\n"
        "`/priority 1 high`\n"
        "`/due 1 25-04`\n"
        "`/remind 1 2hour`\n\n"
        "📝 *Exams:*\n"
        "`/addexam Math 25-04`\n"
        "`/exams`\n\n"
        "📒 *Notes:*\n"
        "`/note Math Newton laws`\n"
        "`/notes Math`\n\n"
        "⏱️ `/studytimer`\n"
        "📊 `/progress`\n\n"
        "🤖 *AI:*\n"
        "`/aisummary [text]`\n"
        "`/mindmap [topic]`\n"
        "Photo bhejo → Auto summary!",
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
    app.add_handler(CommandHandler("priority", set_priority))
    app.add_handler(CommandHandler("due", set_due))
    app.add_handler(CommandHandler("remind", remind))
    app.add_handler(CommandHandler("addexam", addexam))
    app.add_handler(CommandHandler("exams", show_exams))
    app.add_handler(CommandHandler("note", add_note))
    app.add_handler(CommandHandler("notes", show_notes))
    app.add_handler(CommandHandler("studytimer", study_timer))
    app.add_handler(CommandHandler("progress", progress))
    app.add_handler(CommandHandler("aisummary", ai_summary))
    app.add_handler(CommandHandler("mindmap", mind_map))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot start ho gaya!")
    app.run_polling()

if __name__ == "__main__":
    main()
