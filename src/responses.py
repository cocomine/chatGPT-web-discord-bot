import discord
from requests.exceptions import ChunkedEncodingError
from revChatGPT.V1 import Chatbot
from dotenv import load_dotenv
import os

from urllib3.exceptions import InvalidChunkLength

from src import log
import functools
import typing
import asyncio
from src import bot

# start up
logger = log.setup_logger(__name__)

load_dotenv()
openAI_email = os.getenv("OPENAI_EMAIL")
openAI_pass = os.getenv("OPENAI_PASSWORD")
conversation = None
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


async def handle_response(user_message: str, message: discord.Message = None, isreplyall=False,
                          channel: discord.TextChannel = None):
    global conversation
    prev_msg = ""
    my_message = None

    if channel is None and message is not None:
        channel = message.channel

    if message is None:
        my_message = await channel.send("> Response generating, please wait for moment...")
    else:
        if isreplyall:
            my_message = await message.reply("> Response generating, please wait for moment...")
        else:
            my_message = await message.followup.send("> Response generating, please wait for moment...")

    response = chatbot.ask(user_message, conversation_id=conversation)
    try:
        for data in response:
            async with channel.typing():
                output_msg = data["message"]  # get response
                conversation = data['conversation_id']

                if len(output_msg) > 0:
                    if len(output_msg) > 1900:
                        output_msg = output_msg[len(prev_msg):]

                        if isreplyall:
                            my_message = await my_message.reply(output_msg)
                        else:
                            my_message = await message.followup.send(output_msg)
                    else:
                        prev_msg = output_msg
                        await my_message.edit(content=output_msg)
    except ChunkedEncodingError as ex:
        print(f"Invalid chunk encoding {str(ex)}")

    if isreplyall:
        await my_message.reply("> Response has ended.")
    else:
        await message.followup.send("> Response has ended.")

    if message is not None:
        logger.info(f"\x1b[31m{message.author}\x1b[0m : '{user_message}' ({str(channel)}) finish respond")


def reset():
    global conversation
    chatbot.reset_chat()
    conversation = None
