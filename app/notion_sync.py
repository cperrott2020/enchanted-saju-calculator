from __future__ import annotations
import os
from typing import Any
import httpx

class NotionSync:
    def __init__(self):
        self.token=os.getenv("NOTION_TOKEN")
        self.people_ds=os.getenv("NOTION_PEOPLE_DATA_SOURCE_ID")
        self.charts_ds=os.getenv("NOTION_CHARTS_DATA_SOURCE_ID")
        self.cycles_ds=os.getenv("NOTION_LUCK_CYCLES_DATA_SOURCE_ID")
        self.version=os.getenv("NOTION_VERSION","2025-09-03")
    @property
    def configured(self): return bool(self.token and self.people_ds and self.charts_ds)
    def headers(self): return {"Authorization":f"Bearer {self.token}","Notion-Version":self.version,"Content-Type":"application/json"}
    async def create_page(self,ds,props):
        async with httpx.AsyncClient(timeout=30) as c:
            r=await c.post("https://api.notion.com/v1/pages",headers=self.headers(),json={"parent":{"type":"data_source_id","data_source_id":ds},"properties":props})
            r.raise_for_status(); return r.json()
    async def save_verified_chart(self,result:dict[str,Any]):
        if not self.configured: raise RuntimeError("Notion sync is not configured")
        name=result["identity"].get("name") or "Unnamed Saju Profile"; b=result["birth"]; p=result["pillars"]
        rich=lambda x:{"rich_text":[{"type":"text","text":{"content":str(x)[:1900]}}]}
        title=lambda x:{"title":[{"type":"text","text":{"content":str(x)[:1900]}}]}
        person=await self.create_page(self.people_ds,{"Name":title(name),"Person Type":{"select":{"name":"Casual Reading"}},"Birth Date":{"date":{"start":b["original_date"]}},"Birth Time":rich(b["original_time"] or "Unknown"),"Birthplace":rich(b.get("place_label",""))})
        chart=await self.create_page(self.charts_ds,{"Chart Name":title(f"{name} — Natal Chart"),"Status":{"select":{"name":"Verified"}},"Birth Date":{"date":{"start":b["original_date"]}},"Recorded Birth Time":rich(b["original_time"] or "Unknown"),"Corrected Time":rich(b["corrected_solar_local"]),"Birthplace":rich(b.get("place_label","")),"Timezone":rich(b["iana_timezone"]),"Year Pillar":rich(p["year"]["label"]),"Month Pillar":rich(p["month"]["label"]),"Day Pillar":rich(p["day"]["label"]),"Hour Pillar":rich(p["hour"]["label"] if p["hour"] else "Unknown"),"Calculation Version":rich(result["engine"]["version"]),"Calculation Reference":rich(result["engine"]["calculation_reference"]),"Boundary Warning":{"checkbox":bool(result["boundary_check"]["boundary_sensitive"])},"Person":{"relation":[{"id":person["id"]}]}})
        return {"person_page_id":person["id"],"chart_page_id":chart["id"]}
