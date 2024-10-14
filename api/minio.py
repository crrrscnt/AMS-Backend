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


def add_image(spaceobject, pic, path):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    i = spaceobject.pk
    image_name = f'{i}.png'
    if pic == None:
        return Response({'error': f'No image file given for {path}'})
    result = process_file_upload(pic, client, image_name, path)

    if 'error' in result:
        return Response(result)

    if path == 'images':
        spaceobject.img = result
    else:
        spaceobject.setImg = result
    spaceobject.save()
    return Response({'status': 'success'})


def delete_image(spaceobject):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )

    url1 = spaceobject.image_url
    url1 = '/'.join(url1.split('/')[4:])

    res = process_file_delete(client, url1)
    if 'error' in res:
        return Response(res)

    return Response({'status': 'success'})
