import json
import requests
from PIL import Image
import io


# Cloudflare API credentials
ACCOUNT_ID = "074f2dec7dce93bbd2cda2fa339fd467"
AUTH_TOKEN = "jyN1FIk7C9auWxDg40iFPqV3H0Is5giYRxrWmyIO"
API_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/"
)



def image_input(state: dict) -> dict:
    image_path = state["image"]
    
    image_bytes = state["image_bytes"]
    
    if image_bytes:
        return {"image_data": image_path}
    
    image = Image.open(image_path)

    bytes_io = io.BytesIO()
    image.save(bytes_io, format=image.format)

    return {"image_data": list(bytes_io.getvalue())}

def object_detection(state: dict) -> dict:
    # Load the YOLOv8 model (pretrained on COCO dataset)
    image_data = state["image_data"]

    
    prompt = '''
        Identify the objects present in the image.
        give the response in list of JSON format. Just a list of JSON objects. nothing else.
        Provide a list of objects in the following JSON format:
        [
            {
                "name": "name of item",
                "description": "description about the item",
                "quantity": quantity
            }
        ]
    '''
    
    model = "@cf/meta/llama-3.2-11b-vision-instruct"
    
    response = requests.post(
        API_URL + model,
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        json={
            "messages": [
                {"role": "system", "content": "You are a object intifier. You have an image and you need to identify 5 main objects in the image. give the response in JSON format. Just a list of JSON objects. nothiing else."},
                {"role": "user", "content": prompt}
            ],
            "image": image_data,
            "max_tokens": 5000,
            "response_format":{"type": "json"}
        }
    )
    
    
    print(response.json())
    
    
    # Process response
    result = response.json()
    response_text = result.get("result", {}).get("response", "")
    
    print(response_text)
    
    json_data_start = response_text.find("[")
    json_data_end = response_text.rfind("]") + 1
    
    print(response_text[json_data_start:json_data_end])
    
    try:

        objects = json.loads(response_text[json_data_start:json_data_end])
        
    except json.JSONDecodeError:
        
        model = "@cf/meta/llama-3-8b-instruct-awq"
        
        system_prompt = '''
        rewrite the given data into following format
        [
            {
                "name": "name of item",
                "description": "description about the item",
                "quantity": quantity (int)
            }
        ]
        give the response in list of JSON format. Just a list of JSON objects. nothiing else.
        '''
        
        response = requests.post(
            API_URL + model,
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": response_text}
                ],
                "max_tokens": 5000,
                "response_format":{"type": "json"}
            }   
        )
        
        print(response.json())
        
        result = response.json()
        response_text = result.get("result", {}).get("response", "")
        
        print(response_text)
        
        json_data_start = response_text.find("[")
        json_data_end = response_text.rfind("]") + 1
        
        print(response_text[json_data_start:json_data_end])
        
        try:
        
            objects = json.loads(response_text[json_data_start:json_data_end])
        except:
            raise Exception("You are Fucked")
        
    
    print(objects)

    return {"objects": objects}

def price_estimation(state: dict) -> dict:
    
    
    print("-"*50)
    objects = state["objects"]
    
    model = "@cf/meta/llama-3-8b-instruct-awq"
    
    system_prompt = '''
        You are a price estimator. You have a list of items in your store and their descreption
        and your task is to estimate the price of each item in dollars.
        give the response in JSON format. Just a list of JSON objects. nothiing else.
        Provide a list of prices in the following list of JSON format:
        [
            {
                "name": "name of item",
                "price": price (float)
            }
        ]
    '''
    
    response = requests.post(
        API_URL + model,
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        json={
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(objects)}
            ],
            "max_tokens": 5000,
            "response_format":{"type": "json"}
        }
    )
    
    print(response.json())
    
    result = response.json()
    response_text = result.get("result", {}).get("response", "")
    
    print(response_text)
    
    json_data_start = response_text.find("[")
    json_data_end = response_text.rfind("]") + 1

    price_data = json.loads(response_text[json_data_start:json_data_end])
    
    print(price_data)
    print("-"*50)
    
    
    return {"price_data": price_data}

def loss_estimation(state: dict) -> dict:
    with open("disaster_types.json", "r") as f:
        disaster_list = json.load(f)
        
    objects = state["objects"]
    
    loss_prob_wrt_each_disastor = {}
    
    
    for disaster in disaster_list:
    
        prompt = f'''
        objects = {objects}
        disaster = {disaster}
        '''
    
    
        model = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    
        system_prompt = '''
            You are a intelligent damage predictor. You have a list of items in your store and you want to estimate the loss of each item in case of a given disaster.
            for each iteam report the loss in case in tems of range of 0 to 1, telling the probability of loss in case of a disaster.
            Dont response python code , give the response in JSON format. Just a list of JSON objects. nothiing else.
            Provide a list of prices in the following JSON format:
            [
                {
                    "name": "item name",
                    "probability": probability (float)
                }
            ]
            
        '''
            
        response = requests.post(
            API_URL + model,
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": str(prompt)}
                ],
                "max_tokens": 6000,
                "response_format":{"type": "json"}
            }
        )
    
        result = response.json()
        
        print(result)
        
        response_text = result.get("result", {}).get("response", "")
        
        print(response_text)
        json_data_start = response_text.find("[")
        json_data_end = response_text.rfind("]") + 1

        loss_prob_wrt_disastor = json.loads(response_text[json_data_start:json_data_end])
        
        print(loss_prob_wrt_disastor)
        
        loss_prob_wrt_each_disastor[disaster] = loss_prob_wrt_disastor
        
    print(loss_prob_wrt_each_disastor)
    
    return {
        "loss_prob_wrt_disastor": loss_prob_wrt_each_disastor
    }
