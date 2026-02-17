"""
Static list of US and NATO military bases for the map layer. From reference globalthreatmap.
"""
from __future__ import annotations

from typing import List, TypedDict


class MilitaryBase(TypedDict):
    country: str
    baseName: str
    latitude: float
    longitude: float
    type: str  # "usa" | "nato"


MILITARY_BASES: List[MilitaryBase] = [
    {"country": "Germany", "baseName": "Ramstein Air Base", "latitude": 49.4369, "longitude": 7.6003, "type": "usa"},
    {"country": "Germany", "baseName": "Spangdahlem Air Base", "latitude": 49.9725, "longitude": 6.6925, "type": "usa"},
    {"country": "Japan", "baseName": "Kadena Air Base", "latitude": 26.3516, "longitude": 127.7692, "type": "usa"},
    {"country": "Japan", "baseName": "Yokota Air Base", "latitude": 35.7485, "longitude": 139.3487, "type": "usa"},
    {"country": "South Korea", "baseName": "Camp Humphreys", "latitude": 36.9631, "longitude": 127.0311, "type": "usa"},
    {"country": "South Korea", "baseName": "Osan Air Base", "latitude": 37.0906, "longitude": 127.0303, "type": "usa"},
    {"country": "Italy", "baseName": "Aviano Air Base", "latitude": 46.0319, "longitude": 12.5965, "type": "usa"},
    {"country": "United Kingdom", "baseName": "RAF Lakenheath", "latitude": 52.4093, "longitude": 0.5610, "type": "usa"},
    {"country": "United Kingdom", "baseName": "RAF Mildenhall", "latitude": 52.3617, "longitude": 0.4864, "type": "usa"},
    {"country": "Spain", "baseName": "Naval Station Rota", "latitude": 36.6453, "longitude": -6.3497, "type": "usa"},
    {"country": "Turkey", "baseName": "Incirlik Air Base", "latitude": 37.0017, "longitude": 35.4259, "type": "usa"},
    {"country": "Qatar", "baseName": "Al Udeid Air Base", "latitude": 25.1173, "longitude": 51.3150, "type": "usa"},
    {"country": "Kuwait", "baseName": "Camp Arifjan", "latitude": 28.9347, "longitude": 48.0917, "type": "usa"},
    {"country": "Bahrain", "baseName": "NSA Bahrain", "latitude": 26.2361, "longitude": 50.6508, "type": "usa"},
    {"country": "United Arab Emirates", "baseName": "Al Dhafra Air Base", "latitude": 24.2481, "longitude": 54.5467, "type": "usa"},
    {"country": "Djibouti", "baseName": "Camp Lemonnier", "latitude": 11.5469, "longitude": 43.1556, "type": "usa"},
    {"country": "United States", "baseName": "Fort Liberty (Bragg)", "latitude": 35.1400, "longitude": -79.0064, "type": "usa"},
    {"country": "United States", "baseName": "Naval Station Norfolk", "latitude": 36.9461, "longitude": -76.3033, "type": "usa"},
    {"country": "United States", "baseName": "Nellis AFB", "latitude": 36.2361, "longitude": -115.0344, "type": "usa"},
    {"country": "Guam", "baseName": "Andersen Air Force Base", "latitude": 13.5839, "longitude": 144.9244, "type": "usa"},
    {"country": "Australia", "baseName": "Pine Gap", "latitude": -23.7990, "longitude": 133.7370, "type": "usa"},
    {"country": "Iceland", "baseName": "Keflavik Air Base", "latitude": 63.9850, "longitude": -22.6056, "type": "nato"},
    {"country": "Belgium", "baseName": "NATO HQ Brussels", "latitude": 50.8770, "longitude": 4.4260, "type": "nato"},
    {"country": "Poland", "baseName": "Redzikowo Aegis Ashore", "latitude": 54.4791, "longitude": 17.0975, "type": "nato"},
    {"country": "Romania", "baseName": "Mihail Kogălniceanu Air Base", "latitude": 44.3622, "longitude": 28.4883, "type": "nato"},
    {"country": "Italy", "baseName": "NAS Capodichino", "latitude": 40.8831, "longitude": 14.2908, "type": "nato"},
    {"country": "Turkey", "baseName": "Izmir Air Station", "latitude": 38.4192, "longitude": 27.1578, "type": "nato"},
]
