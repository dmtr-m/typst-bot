import os
import logging
from uuid import uuid4
from telegram import (
    InlineQueryResultArticle, 
    InputTextMessageContent, 
    InlineQueryResultPhoto,
)
from telegram.ext import (
    InlineQueryHandler, 
    CommandHandler, 
    ApplicationBuilder, 
    MessageHandler,
    filters,
)
import typst_processing
import requests
import base64
import api_secrets
import history_managment


logging.basicConfig(
    format = '%(asctime)s - %(levelname)s - %(message)s', 
    level = logging.WARNING,
)
logger = logging.getLogger(__name__)

history = history_managment.history()


async def start(update, _):
    await update.message.reply_text(
        'Hello! Use me in inline mode: \
            @typst_bot <your formula without $ here>'
    )


def TYPST_COMPILATION_ERROR_MESSAGE():
    """
    Composes Error message to the inline mode
    """
    error_discription = [
        InlineQueryResultArticle(
            id = uuid4(),
            title = "Error",
            description = f"Error while compiling your Typst code.",
            input_message_content = InputTextMessageContent(
                message_text = \
                    f"Error while compiling your Typst code."
            ),
        )
    ]
    return error_discription


def TYPST_COMPILATION_ERROR_MESSAGE_WITH_SUGGESTION(suggestion=''):
    """
    Composes Error message to the inline mode
    """
    error_discription = [
        InlineQueryResultArticle(
            id = uuid4(),
            title = "Error",
            description = f"Error while compiling your Typst code:\
                \n{suggestion}.",
            input_message_content = InputTextMessageContent(
                message_text = \
                    f"Error while compiling your Typst code: \n{suggestion}."
            ),
        )
    ]
    return error_discription


def PHOTO_RESULT_MESSAGE(photo_details: dict, photo_size: tuple):
    """
    Generates message with image as an option to user
    input: 
        dict: ("photo_url": str, "thumbnail_url": str) - image parameters,  
        tuple: (int, int) - image size
    """
    in_line_query_message = [
        InlineQueryResultPhoto(
            id = uuid4(),
            photo_url = photo_details["photo_url"],
            thumbnail_url = photo_details["thumbnail_url"],
            title = "Typst image",
            photo_width = photo_size[0],
            photo_height = photo_size[1],
        )
    ]
    return in_line_query_message


def upload_photo(photo_bytes):
    """
    Uploads image to the hosting
    input: bytes (png)
    output: dict ("photo_url": str, "thumbnail_url": str) - image parameters
    """
    HOSTING_URL = "https://api.imgbb.com/1/upload"

    image_and_key = {
        "key": api_secrets.IMG_API,
        "image": base64.b64encode(photo_bytes),
    }
    
    hosting_response = requests.post(HOSTING_URL, image_and_key)
    if hosting_response.status_code == 200:
        return {
            "photo_url": hosting_response.json()["data"]["url"],
            "thumbnail_url": hosting_response.json()["data"]["thumb"]["url"],
        }
    
    return None


async def inlinequery(update, _) -> None:
    query = update.inline_query.query
    if query:
        try:
            image_bytes, size = typst_processing.generate_image(query)
            uploaded_photo_details = upload_photo(image_bytes)
            result_message = PHOTO_RESULT_MESSAGE(uploaded_photo_details, size)
            await update.inline_query.answer(
                result_message, 
                cache_time=1,
            )
            # Remebering last query
            senders_id = update.inline_query.from_user.id
            history.new_query(senders_id, query)

        except Exception as e:
            # logger.warning(e)    # This error is only used for suggestions
            ### Needs to be fixed
            if len(e.args) > 0 and e.args[0].startswith('error:'):
                suggestion = e.args[0].split('\n')[0]
                error_message = TYPST_COMPILATION_ERROR_MESSAGE_WITH_SUGGESTION(
                    suggestion.capitalize()
                )
            else:
                error_message = TYPST_COMPILATION_ERROR_MESSAGE()

            await update.inline_query.answer(
                error_message, 
                cache_time=1,
            )


async def last_query(update, _):
    query = history.recent_query(update.message.chat.id)
    if query == 0:
        await update.message.reply_text(
            '*Sorry...\nThere are no recent queries stored*',
            parse_mode='MarkdownV2',
        )
    else:
        await update.message.reply_text(
            'This is your previous query:',
            parse_mode='MarkdownV2',
        )
        query = query.replace('(', '\(').replace(')', '\)').replace('`', '\`')
        await update.message.reply_text(
            f'`{query}`',
            parse_mode='MarkdownV2'
        )


async def query_through_message(update, _):
    query = update.message.text
    try:
        image_bytes, _ = typst_processing.generate_image(query)
        await update.message.reply_photo(image_bytes)

    except Exception as e:
        # logger.warning(e)   # This error is only used for suggestions
        ### Needs to be fixed
        suggestion = ''
        if len(e.args) > 0 and e.args[0].startswith('error:'):
            suggestion = e.args[0].split('\n')[0]
            suggestion = suggestion.capitalize()

        await update.message.reply_text(
            f'*Error while compiling your Typst code\.* \
                \n\n{suggestion}',
            parse_mode='MarkdownV2',
        )


if __name__ == '__main__':
    app = ApplicationBuilder().token(api_secrets.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("last_query", last_query))
    app.add_handler(MessageHandler(filters.TEXT, query_through_message))
    app.add_handler(InlineQueryHandler(inlinequery))

    app.run_polling()
