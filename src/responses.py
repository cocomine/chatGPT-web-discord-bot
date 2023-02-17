import discord
from revChatGPT.V1 import Chatbot
from dotenv import load_dotenv
import os
from src import log
import functools
import typing
import asyncio

logger = log.setup_logger(__name__)

load_dotenv()
openAI_email = os.getenv("OPENAI_EMAIL")
openAI_pass = os.getenv("OPENAI_PASSWORD")
chatbot = Chatbot(config={
    "email": openAI_email,
    "password": openAI_pass
})


def thread_ask(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


@thread_ask
def ask(prompt):
    return chatbot.ask(prompt)


async def handle_response(user_message: str, message: discord.Message, isreplyall=False,
                          channel: discord.TextChannel = None):
    prev_msg = ""
    my_message = None
    author = ""

    if message is not None:
        author = "<@" + str(message.author.id) + ">"

    if channel is None:
        channel = message.channel

    async with channel.typing():
        respone = await ask(user_message)
        for data in respone:
            output_msg = data["message"][len(prev_msg):]  # get response

            if len(output_msg) > 1900:
                if my_message is None:
                    if message is None and channel is not None:
                        my_message = await channel.send(output_msg)
                    else:
                        if isreplyall:
                            my_message = await message.reply(output_msg)
                        else:
                            my_message = await message.followup.send(output_msg)
                else:
                    if len(output_msg) > 1900:
                        output_msg = output_msg[len(prev_msg):]

                        if message is None and channel is not None:
                            my_message = await channel.send(output_msg)
                        else:
                            if isreplyall:
                                my_message = await message.reply(output_msg)
                            else:
                                my_message = await message.followup.send(output_msg)
                    else:
                        prev_msg = output_msg
                        await my_message.edit(content=output_msg)

    logger.info(f"\x1b[31m{author}\x1b[0m : '{user_message}' ({str(channel)}) finish respond")
    await channel.send(f"> Response has ended. {author}")
