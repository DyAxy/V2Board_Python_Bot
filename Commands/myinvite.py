import bot
from handler import MysqlUtils
from telegram import Update
from telegram.ext import ContextTypes

desc = '获取我的使用信息'
config = bot.config['bot']


def onQuery(uid):
    try:
        db = MysqlUtils()
        result1 = db.sql_query(
            'SELECT * FROM v2_invite_code WHERE user_id = %s' % uid)
        result2 = db.count_sql_query(
            'v2_user', sql_condition='WHERE invite_user_id = %s' % uid)
    finally:
        db.close()
        return result1, result2


def getContent(uid):
    code, times = onQuery(uid)
    text = '❌*错误*\n你还没有生成过邀请码，点击前往网站生成一个吧！'
    if len(code) > 0:
        header = '📚*邀请信息*\n\n🔮邀请地址为（点击即可复制）：\n'
        tolink = '`%s/#/register?code=%s`' % (
            config['website'], code[0][2])
        buttom = '\n\n👪*邀请人数：* %s' % times
        text = f'{header}{tolink}{buttom}'

    return text


async def autoDelete(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.delete_message(job.chat_id, job.data)


async def exec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    user_id = msg.from_user.id
    chat_id = msg.chat_id
    chat_type = msg.chat.type
    try:
        db = MysqlUtils()
        user = db.sql_query(
            'SELECT * FROM v2_user WHERE `telegram_id` = %s' % user_id)
        if chat_type == 'private' or chat_id == config['group_id']:
            if len(user) > 0:
                text = getContent(user[0][0])
                callback = await msg.reply_markdown(text)
            else:
                callback = await msg.reply_markdown('❌*错误*\n你还没有绑定过账号！')
            if chat_type != 'private':
                context.job_queue.run_once(
                    autoDelete, 15, data=callback.message_id, chat_id=chat_id, name=str(callback.message_id))
    finally:
        db.close()