from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
import boto3
from botocore.exceptions import ClientError

app = FastAPI()
s3_client = boto3.client('s3')

# Configura aquí el nombre exacto de tu bucket de AWS
BUCKET_NAME = "finalso-fastapi-s3-bucket"

# --- ENDPOINT POST (Puntos a, b, c) ---
@app.post("/upload/")
async def upload_image(username: str = Form(...), file: UploadFile = File(...)):
    # Validación de formato (Punto b)
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato inválido. Solo se acepta PNG o JPG/JPEG."
        )
    
    # Organización de archivos por usuario (Punto c)
    s3_key = f"{username}/{file.filename}"
    
    try:
        s3_client.upload_fileobj(file.file, BUCKET_NAME, s3_key)
        return {"status": "success", "s3_path": s3_key}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINT GET (Puntos d, e) ---
@app.get("/download/")
async def get_image_url(username: str, filename: str):
    s3_key = f"{username}/{filename}"
    
    try:
        # Verificar existencia y obtener metadatos (Punto e)
        metadata = s3_client.head_object(Bucket=BUCKET_NAME, Key=s3_key)
        storage_date = metadata.get('LastModified')
        
        # Generar URL pre-firmada válida (Punto e)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600
        )
        
        return {
            "exists": True,
            "storage_date": storage_date,
            "url": presigned_url
        }
        
    except ClientError as e:
        # Si no existe, retorna mensaje claro (Punto e)
        if e.response.get('Error', {}).get('Code') == '404':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El usuario '{username}' o la imagen '{filename}' no existen en S3."
            )
        raise HTTPException(status_code=500, detail=str(e))
