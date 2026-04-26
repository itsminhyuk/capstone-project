# api/map.py
from fastapi import APIRouter
import requests

router = APIRouter()
KAKAO_KEY = "YOUR_KAKAO_REST_API_KEY"

@router.get("/pharmacies")
async def get_pharmacies(lat: float, lng: float):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_KEY}"}
    params = {"query": "약국", "x": lng, "y": lat, "radius": 2000}
    return requests.get(url, headers=headers, params=params).json()

@router.get("/waste-bins")
async def get_bins():
    # DB에서 수거함 데이터를 가져옵니다.
    bins = db.query(DisposalBin).all()
    
    # 프론트엔드 yakpool_app_v8.html은 'place_name'이라는 키를 사용하므로 이름을 맞춰서 반환합니다.
    return [
        {
            "place_name": bin.name, # DB의 name을 프론트엔드의 place_name으로 매핑
            "address": bin.address,
            "lat": bin.lat,
            "lng": bin.lng
        } for bin in bins
    ]
