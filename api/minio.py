from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *


def process_file_upload(file_object: InMemoryUploadedFile, client, image_name,
                        bucket_name):
    try:
        object_name = f"{bucket_name}/{image_name}" if bucket_name != 'images' else image_name
        client.put_object('images', object_name, file_object, file_object.size)
        return f'http://localhost:9000/images/{object_name}'
    except Exception as e:
        return {'error': str(e)}


def process_file_delete(client, image_name):
    try:
        client.remove_object('images', image_name)
        return {'status': 'success'}
    except Exception as e:
        return {'error': str(e)}



def add_pic(new_stock, pic, bucket_name):
    client = Minio(
            endpoint=settings.AWS_S3_ENDPOINT_URL,
           access_key=settings.AWS_ACCESS_KEY_ID,
           secret_key=settings.AWS_SECRET_ACCESS_KEY,
           secure=settings.MINIO_USE_SSL
    )
    i = new_stock.id
    img_obj_name = f"{i}.jpg"
    if not pic:
        return Response({"error": "Нет файла для изображения логотипа."})
    result = process_file_upload(pic, client, img_obj_name, bucket_name)

    if 'error' in result:
        return Response(result)

    new_stock.url = result
    new_stock.save()

    return Response({"message": "success"})


def delete_image(spaceobject):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )

    url1 = spaceobject.image_url
    url1 = '/'.join(url1.split('/')[4:])

    #url2 = spaceobject.setImg
    #url2 = '/'.join(url2.split('/')[4:])

    #     url1 = spaceobject.img.split('/')[-1]  # Получаем только имя файла
    #     url2 = spaceobject.setImg.split('/')[-1]  # Получаем только имя файла

    res = process_file_delete(client, url1)
    if 'error' in res:
        return Response(res)

    #res = process_file_delete(client, url2)
    #if 'error' in res:
    #    return Response(res)

    return Response({'status': 'success'})
