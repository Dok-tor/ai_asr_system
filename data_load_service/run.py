import tempfile

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response


import s3_module as s3


app = FastAPI()


@app.post("/upload-to-s3/")
async def predict(file: UploadFile = File(...), filename: str = Form(...), transcription: str = Form(...)):
    try:
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_file:
            temp_file.write(await file.read())
            temp_file.flush()
            file_location = temp_file.name
            result = await s3.upload_to_s3(file_location, transcription, filename)
            if result:
                return Response(status_code=200)
            else:
                raise HTTPException(status_code=500, detail="Failed to upload to S3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-all-files/")
async def download_files():
    try:
        await s3.download_all_files_from_s3()
        return Response(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
