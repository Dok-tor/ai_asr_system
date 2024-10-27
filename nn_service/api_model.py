import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
import os
import tempfile
import logging


from transformers import pipeline

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Инициализируем модель
pipe = pipeline(task="automatic-speech-recognition", model="./whisper-small-ru", device=device)


app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f'device: {device}')


# Эндпоинт для предсказаний на основе аудиофайла
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:

        # await asyncio.sleep(0)  # Отправляем немедленно
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(await file.read())
            temp_file.flush()
            file_location = temp_file.name

        # Используем модель для транскрипции
        transcription = pipe(file_location, return_timestamps=True)["text"]
        logging.info(transcription)

        # current_time = datetime.now()
        # # Формируем строку в нужном формате (например, YYYY-MM-DD_HH-MM-SS)
        # filename = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        # logging.info(f'filename: {filename}, file: {file_location}')

        # upload_to_s3(audio_file_path=file_location, transcription_text=transcription, file_name=file.filename)

        # Удаляем временный файл
        os.remove(file_location)

        return {"prediction": transcription}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
