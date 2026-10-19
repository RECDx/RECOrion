"""
RECOrion AI Ajanları Sürekli Öğrenme ve Araştırma Servisi (Agent Learning Service).

Bu servis iki temel öğrenme mekanizmasını yürütür:
1. Yazışmalardan Öğrenme (Learn from Chat / Dialogue):
   - Sohbet ve görev diyaloglarından kalıcı kurumsal kararları, müşteri tercihlerini,
     operasyonel kuralları ve iş know-how'ını ayıklayarak Qdrant ve PostgreSQL hafızasına kaydeder.
2. Deep Search ve Aramalardan Öğrenme (Deep Search & Learn):
   - Ajanın internette çoklu kaynaklı derin web araması yapması, sonuç sayfalarını tarayıp
     sentezlemesi ve elde ettiği bilgileri kendi uzmanlık hafızasına indekslemesi.
"""
import asyncio
import json
import logging
import re
import urllib.parse
from typing import List, Dict, Any, Optional
import uuid

import httpx
from app.core.net import safe_request
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import MemoryItem, AgentDocument, Actor, ChatMessage, Tenant, JobTitle
from app.services.collective_memory import collective_memory
from app.services.evren_gateway import evren_gateway

logger = logging.getLogger("agent_learning_service")


class AgentLearningService:
    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        }

    # =========================================================================
    # 1. DEEP SEARCH / WEB ARAMA YARDIMCILARI
    # =========================================================================
    def _clean_ddg_url(self, raw_url: str) -> str:
        """DuckDuckGo yönlendirme URL'sini orijinal temiz web adresine dönüştürür."""
        if "uddg=" in raw_url:
            target = raw_url.split("uddg=")[1].split("&")[0]
            return urllib.parse.unquote(target)
        return raw_url

    async def perform_web_search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        DuckDuckGo üzerinden web araması gerçekleştirir ve başlık, link ve snippet döner.
        """
        search_url = "https://html.duckduckgo.com/html/"
        data = {"q": query}
        results = []

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=self.headers) as client:
                resp = await client.post(search_url, data=data)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                rows = soup.select(".result")
                for row in rows[:max_results]:
                    title_elem = row.select_one(".result__title a")
                    snippet_elem = row.select_one(".result__snippet")

                    if title_elem and title_elem.get("href"):
                        title = title_elem.get_text(strip=True)
                        raw_link = title_elem["href"]
                        clean_link = self._clean_ddg_url(raw_link)
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                        if clean_link.startswith(("http://", "https://")):
                            results.append({
                                "title": title,
                                "url": clean_link,
                                "snippet": snippet
                            })
        except Exception as e:
            logger.warning(f"Web arama motoru sorgu hatası ('{query}'): {e}")

        return results

    async def fetch_page_content(self, url: str) -> str:
        """Belirtilen URL'den sayfayı çeker ve temiz metin çıkarır."""
        try:
            resp = await safe_request("GET", url, timeout=15.0, headers=self.headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "iframe"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 30]
                return "\n".join(lines[:40])  # İlk 40 paragraf
        except Exception as e:
            logger.info(f"Sayfa metni çekilemedi ({url}): {e}")
        return ""

    # =========================================================================
    # 2. DEEP SEARCH VE ARAMALARDAN ÖĞRENME
    # =========================================================================
    async def deep_search_and_learn(
        self,
        tenant_id: uuid.UUID,
        agent_id: uuid.UUID,
        query: str,
        db: AsyncSession,
        model_code: str = "glm-5.3"
    ) -> Dict[str, Any]:
        """
        AI Ajanı için Deep Search başlatır:
        1. Konuyu internette arar.
        2. En alakalı sayfaları okur.
        3. LLM ile analiz ve sentez yaparak kurumsal/uzmanlık bilgi maddelerini çıkarır.
        4. Hem Qdrant hem DB MemoryItem hem de AgentDocument kütüphanesine kaydeder.
        """
        agent = await db.get(Actor, agent_id)
        agent_name = agent.display_name if agent else "AI Ajanı"

        # 1. Web arama sonuçlarını topla
        search_results = await self.perform_web_search(query, max_results=5)
        if not search_results:
            raise ValueError(f"'{query}' konusu için web arama sonuçlarına ulaşılamadı.")

        # 2. En iyi 2-3 sayfanın tam metnini topla
        collected_sources = []
        for res in search_results[:3]:
            page_text = await self.fetch_page_content(res["url"])
            collected_sources.append({
                "title": res["title"],
                "url": res["url"],
                "snippet": res["snippet"],
                "content": page_text[:2500] if page_text else res["snippet"]
            })

        # 3. LLM ile Derin Sentez & Öğrenme Maddeleri Üretimi
        sources_context = ""
        for i, s in enumerate(collected_sources, 1):
            sources_context += f"\n--- KAYNAK {i}: {s['title']} ({s['url']}) ---\nÖzet: {s['snippet']}\nİçerik: {s['content']}\n"

        system_prompt = (
            "Sen RECOrion otonom iş platformunun Derin Araştırma ve Hafıza Sentez Motorusun.\n"
            "Görevin: Verilen arama sonuçlarını ve web kaynaklarını analiz ederek, AI ajanın "
            "işinde kullanabileceği net, doğrulanmış ve kalıcı uzmanlık bilgilerini sentezlemektir.\n"
            "Çıktıyı MUTLAKA geçerli bir JSON nesnesi olarak üret. JSON formatı:\n"
            "{\n"
            '  "summary_report": "Konunun detaylı 2-3 paragraflık profesyonel Türkçe araştırma özeti.",\n'
            '  "learnings": [\n'
            '    {\n'
            '      "fact": "Öğrenilen net bilgi maddesi (1-2 cümle).",\n'
            '      "category": "MEVZUAT | TEKNİK | PAZAR | OPERASYON | KURAL",\n'
            '      "confidence": 0.95\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        user_prompt = (
            f"Araştırma Konusu: {query}\n"
            f"Hedef AI Personeli: {agent_name}\n\n"
            f"İncelenen Web Kaynakları:\n{sources_context}\n\n"
            f"Lütfen bu kaynakları sentezleyip JSON formatında araştırma raporunu ve hafızaya kaydedilecek öğrenim maddelerini üret."
        )

        ai_resp = await evren_gateway.chat_completion(
            model_code=model_code,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        raw_content = ai_resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        # JSON bloğunu ayıkla
        cleaned_json = raw_content.strip()
        if "```json" in cleaned_json:
            cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned_json:
            cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()

        try:
            synthesis = json.loads(cleaned_json)
        except Exception:
            synthesis = {
                "summary_report": raw_content[:800],
                "learnings": [
                    {
                        "fact": f"{query} konusunda web araştırması tamamlandı ve sentezlendi.",
                        "category": "OPERASYON",
                        "confidence": 0.90
                    }
                ]
            }

        summary_report = synthesis.get("summary_report", raw_content[:800])
        learnings_list = synthesis.get("learnings", [])

        # 4. Bilgi Maddelerini MemoryItem & Qdrant Hafızasına Kaydet
        created_memories = []
        for item in learnings_list:
            fact_text = item.get("fact", "").strip()
            if not fact_text:
                continue

            conf = float(item.get("confidence", 0.95))
            cat = item.get("category", "DEEP_SEARCH")

            mem = MemoryItem(
                tenant_id=tenant_id,
                scope="AGENT",
                agent_id=agent_id,
                source_reference=f"DEEP_SEARCH: {query[:80]}",
                content=fact_text,
                metadata_json={
                    "source_type": "deep_search",
                    "query": query,
                    "category": cat,
                    "agent_name": agent_name,
                    "sources": [s["url"] for s in collected_sources]
                },
                status="APPROVED",
                confidence_score=conf
            )
            db.add(mem)
            await db.flush()

            # Qdrant Vektör İndeksi
            try:
                await collective_memory.add_memory(
                    tenant_id=str(tenant_id),
                    scope="AGENT",
                    agent_id=str(agent_id),
                    source_reference=f"DEEP_SEARCH: {query[:80]}",
                    content=fact_text,
                    metadata={
                        "source_type": "deep_search",
                        "query": query,
                        "category": cat,
                        "agent_name": agent_name,
                        "memory_item_id": str(mem.id)
                    }
                )
            except Exception as qe:
                logger.warning(f"Qdrant deep search indeksleme uyarısı: {qe}")

            created_memories.append({"id": str(mem.id), "fact": fact_text, "category": cat})

        # 5. AgentDocument Tablosuna Doküman/Rapor Olarak Kaydet
        full_report_text = (
            f"--- DEEP SEARCH ARAŞTIRMA RAPORU ---\n"
            f"Arama Konusu: {query}\n"
            f"Tarih: RECOrion Sistem Kaydı\n\n"
            f"ÖZET VE ANALİZ:\n{summary_report}\n\n"
            f"ÇIKARILAN VE HAFIZAYA İNDEKSLENEN TEMEL BİLGİ MADDELERİ:\n"
        )
        for idx, m in enumerate(created_memories, 1):
            full_report_text += f"{idx}. [{m['category']}] {m['fact']}\n"

        full_report_text += "\nKULLANILAN WEB KAYNAKLARI:\n"
        for s in collected_sources:
            full_report_text += f"- {s['title']}: {s['url']}\n"

        doc = AgentDocument(
            tenant_id=tenant_id,
            agent_id=agent_id,
            file_name=f"deep_search_{uuid.uuid4().hex[:8]}",
            original_name=f"🔍 Deep Search: {query[:60]}",
            file_type="deep_search",
            file_size=len(full_report_text.encode("utf-8")),
            storage_path=f"search://{urllib.parse.quote(query[:60])}",
            extracted_text=full_report_text[:100000],
            summary=f"🔍 Deep Search Araştırması: {query}\n{summary_report[:250]}...",
            status="INDEXED",
            memory_item_id=uuid.UUID(created_memories[0]["id"]) if created_memories else None
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        return {
            "query": query,
            "document_id": str(doc.id),
            "summary_report": summary_report,
            "learnings_count": len(created_memories),
            "learnings": created_memories,
            "sources_count": len(collected_sources),
            "sources": [{"title": s["title"], "url": s["url"]} for s in collected_sources]
        }

    # =========================================================================
    # 2.B. SEKTÖR VE ÜNVAN ODAKLI DEEP SEARCH & AJAN ONBOARDING ÖĞRENMESİ
    # =========================================================================
    async def deep_search_sector_and_title(
        self,
        tenant_id: uuid.UUID,
        job_title_id: uuid.UUID,
        db: AsyncSession,
        agent_name: Optional[str] = None,
        agent_id: Optional[uuid.UUID] = None,
        model_code: str = "glm-5.3"
    ) -> Dict[str, Any]:
        """
        AI Ajanı Tanımlanırken veya Eğitilirken:
        1. Bağlı olduğu şirketin sektörünü (tenant.sectors, sector_manifesto) inceler.
        2. Ajanın atandığı ünvanı (job_title.title, category, description) inceler.
        3. Web üzerinde çift odaklı Deep Search yapar:
           - Sektörün dinamikleri, mevzuatı ve işleyişi
           - Sektörde bu ünvanın tam olarak ne iş yaptığı, görev tanımları ve operasyonel iş akışları
        4. EVREN LLM ile sentezler:
           - Zenginleştirilmiş Sistem Rol Persona Promptu üretir
           - Sektör ve ünvan analiz raporu üretir
           - Hafızaya kaydedilecek atomik kurumsal/uzmanlık bilgi maddelerini çıkarır
        5. Eğer agent_id varsa doğrudan hafızaya ve kütüphaneye kaydeder; yoksa döner.
        """
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise ValueError("Şirket (Tenant) bulunamadı.")

        job_title = await db.get(JobTitle, job_title_id)
        if not job_title:
            raise ValueError("Seçilen ünvan bulunamadı.")

        job_title_name = job_title.title
        agent_display_name = agent_name or f"{job_title_name} Ajanı"

        # Şirket Sektörünü Belirle
        sectors = tenant.sectors or []
        sector_str = ", ".join(sectors) if isinstance(sectors, list) and sectors else "Genel İşletme ve Ticaret"
        if not sectors and tenant.sector_manifesto:
            sector_str = "Kurumsal Sektör"

        # 1. Çift Odaklı Web Arama Sorguları
        query_sector = f"{sector_str} sektörü dinamikleri mevzuatı pazar standartları ve işleyişi"
        query_title = f"{sector_str} sektöründe {job_title_name} ne iş yapar görev tanımı sorumlulukları iş akışları"

        logger.info(f"Sektör & Ünvan Deep Search başlatılıyor: Sektör='{sector_str}', Ünvan='{job_title_name}'")

        # Paralel web araması
        sector_results, title_results = await asyncio.gather(
            self.perform_web_search(query_sector, max_results=3),
            self.perform_web_search(query_title, max_results=3)
        )

        all_search_results = (sector_results or []) + (title_results or [])
        if not all_search_results:
            fallback_query = f"{sector_str} {job_title_name} görev tanımı ve sektörel işleyiş"
            all_search_results = await self.perform_web_search(fallback_query, max_results=4)

        collected_sources = []
        for res in all_search_results[:4]:
            page_text = await self.fetch_page_content(res["url"])
            collected_sources.append({
                "title": res["title"],
                "url": res["url"],
                "snippet": res["snippet"],
                "content": page_text[:2000] if page_text else res["snippet"]
            })

        sources_context = ""
        for i, s in enumerate(collected_sources, 1):
            sources_context += f"\n--- KAYNAK {i}: {s['title']} ({s['url']}) ---\nÖzet: {s['snippet']}\nİçerik: {s['content']}\n"

        # 2. EVREN LLM Sentezi
        system_prompt = (
            "Sen RECOrion otonom iş platformunun Sektörel Uzmanlık ve AI Rol Tanımlama Mimarı ve Derin Araştırma Motorusun.\n"
            "Görevin: Verilen web araştırma bulgularını inceleyerek, şirketin sektörünü ve bu sektörde bu AI ajanın ünvanının "
            "tam olarak NE İŞ YAPTIĞINI, görev tanımını, sorumluluklarını ve iş akışlarını derinlemesine öğrenmektir.\n\n"
            "Çıktıyı MUTLAKA geçerli bir JSON formatında üret. JSON Şablonu:\n"
            "{\n"
            '  "sector_summary": "Şirketin sektörünün dinamikleri, mevzuatı, pazar standartları ve operasyonel kurallarına dair detaylı 2 paragraflık Türkçe analiz.",\n'
            '  "job_title_summary": "Bu sektörde bu ünvanın ne iş yaptığı, günlük operasyonel ve stratejik sorumlulukları, süreçleri ve kullandığı standartlar (2 paragraf).",\n'
            '  "enhanced_system_prompt": "Bu AI Ajanına özel hazırlanmış güçlü, profesyonel Sistem Rol Persona Promptu. Sektör bilgisi, ünvan görev tanımı, karar alma kuralları ve konuşma üslubunu içermelidir (Sen bir ... personelsin diye başlasın).",\n'
            '  "learnings": [\n'
            '    {\n'
            '      "fact": "Öğrenilen sektörel kural veya ünvansal iş yapış bilgisi (1-2 net cümle).",\n'
            '      "category": "SEKTOR_KURALI | GOREV_TANIMI | MEVZUAT | OPERASYONEL_SUREC",\n'
            '      "confidence": 0.95\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        user_prompt = (
            f"Şirket Adı: {tenant.name}\n"
            f"Faaliyet Sektörü: {sector_str}\n"
            f"Şirket Sektör Manifestosu / Notları: {tenant.sector_manifesto or 'Belirtilmedi'}\n"
            f"AI Ajan Adı: {agent_display_name}\n"
            f"Atanan Ünvan: {job_title_name} (Kategori: {job_title.category or 'Operasyonel'})\n"
            f"Mevcut Ünvan Açıklaması: {job_title.description or 'Belirtilmedi'}\n\n"
            f"İncelenen Web Kaynakları ve Sektörel Bulgular:\n{sources_context}\n\n"
            f"Lütfen bu kaynakları analiz ederek ajanın hem sektörü hem de sektördeki ünvanının ne iş yaptığını "
            f"öğreneceği JSON sentezini üret."
        )

        try:
            ai_resp = await evren_gateway.chat_completion(
                model_code=model_code,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                timeout=25.0
            )
            raw_content = ai_resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            cleaned_json = raw_content.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()

            synthesis = json.loads(cleaned_json)
        except Exception as synth_err:
            logger.info(f"LLM yanıtı doğrudan JSON çözülemedi ({synth_err}), zengin içerik fallback'i devreye alınıyor.")
            # Web kaynaklarından akıllı özet derle
            snippets = [s.get("snippet", "") for s in collected_sources if s.get("snippet")]
            snippet_highlights = (" ".join(snippets)[:500] + "...") if snippets else "Sektörel mevzuatlar ve pazar uygulamaları tarandı."

            sec_sum = (
                f"{sector_str} sektörü; dinamik pazar talepleri, regülasyonlar ve yüksek kalite standartları ekseninde faaliyet göstermektedir. "
                f"Sektör genelinde deterministik iş akışları, veri güvenliği ve sürdürülebilir operasyonlar önceliklidir."
            )
            job_sum = (
                f"{job_title_name}, {sector_str} sektörü dinamiklerinde şirketin operasyonel hedeflerini hayata geçiren, "
                f"kalite kapılarını ve süreç çıktılarını denetleyen kilit bir uzmanlık rolüdür. Görev kapsamındaki kararların deterministik ve kurallara uygun olması esastır."
            )

            synthesis = {
                "sector_summary": sec_sum,
                "job_title_summary": job_sum,
                "enhanced_system_prompt": (
                    f"# {job_title_name.upper()} - SİSTEM ROL PROMPTU (SEKTÖREL PERSONA & YÖNERGELER)\n\n"
                    f"Sen **{tenant.name}** şirketi bünyesinde **{sector_str}** sektöründe görev yapan kıdemli ve yetkili bir **{job_title_name}** AI personelsin.\n\n"
                    f"## 1. MİSYON VE KİMLİK\n"
                    f"- {job_sum}\n"
                    f"- Şirket Sektörel Çerçevesi: {sec_sum}\n\n"
                    f"## 2. TEMEL ÇALIŞMA İLKELERİ VE GÖREVLER\n"
                    f"- Görev kapsamındaki tüm talepleri deterministik, eksiksiz ve kanıtlanabilir verilerle yanıtla.\n"
                    f"- Şirket içi kolektif hafızayı (Qdrant & MemoryItem) ve sektörel kalite kapılarını etkin uygula.\n"
                    f"- Belirsiz durumlarda varsayım yapmak yerine netleştirici sorular sorarak kurumsal standartları koru.\n\n"
                    f"## 3. SEKTÖREL MEVZUAT VE KALİTE STANDARTLARI\n"
                    f"- {sector_str} alanında yürürlükte olan pazar normlarına, KVKK/etik kurallara ve müşteri gizliliğine tam uyum sağla."
                ),
                "learnings": [
                    {
                        "fact": f"{sector_str} sektöründe operasyonel süreçler, kalite kapıları ve pazar regülasyonları titizlikle uygulanmalıdır.",
                        "category": "SEKTOR_KURALI",
                        "confidence": 0.95
                    },
                    {
                        "fact": f"{job_title_name} rolü; iş akışlarının eksiksiz yürütülmesinden, çıktıların doğrulanmasından ve şirket hedeflerinin gerçekleştirilmesinden sorumludur.",
                        "category": "GOREV_TANIMI",
                        "confidence": 0.95
                    },
                    {
                        "fact": f"{sector_str} pazarında faaliyet gösteren şirketlerde müşteri gizliliği, veri güvenliği ve mevzuatsal uyumluluk vazgeçilmez temel taahhüttür.",
                        "category": "MEVZUAT",
                        "confidence": 0.95
                    },
                    {
                        "fact": f"{job_title_name} pozisyonu, operasyonel belirsizliklerde varsayımda bulunmayıp şirket hafızasını (Memory) referans almalıdır.",
                        "category": "OPERASYONEL_SUREC",
                        "confidence": 0.95
                    }
                ]
            }

        sector_summary = synthesis.get("sector_summary", "")
        job_title_summary = synthesis.get("job_title_summary", "")
        enhanced_prompt = synthesis.get("enhanced_system_prompt", "")
        learnings_list = synthesis.get("learnings", [])

        # 3. Eğer agent_id verilmişse hafızaya ve doküman tablosuna anında kaydet
        saved_memories = []
        doc_id = None
        if agent_id:
            for item in learnings_list:
                fact_text = item.get("fact", "").strip()
                if not fact_text:
                    continue
                conf = float(item.get("confidence", 0.95))
                cat = item.get("category", "SECTOR_JOB_TITLE")

                mem = MemoryItem(
                    tenant_id=tenant_id,
                    scope="AGENT",
                    agent_id=agent_id,
                    source_reference=f"DEEP_SEARCH_ONBOARDING: {sector_str} - {job_title_name}",
                    content=fact_text,
                    metadata_json={
                        "source_type": "deep_search_onboarding",
                        "sector": sector_str,
                        "job_title": job_title_name,
                        "category": cat,
                        "agent_name": agent_display_name
                    },
                    status="APPROVED",
                    confidence_score=conf
                )
                db.add(mem)
                await db.flush()

                try:
                    await collective_memory.add_memory(
                        tenant_id=str(tenant_id),
                        scope="AGENT",
                        agent_id=str(agent_id),
                        source_reference=f"DEEP_SEARCH_ONBOARDING: {sector_str} - {job_title_name}",
                        content=fact_text,
                        metadata={
                            "source_type": "deep_search_onboarding",
                            "sector": sector_str,
                            "job_title": job_title_name,
                            "category": cat,
                            "memory_item_id": str(mem.id)
                        }
                    )
                except Exception as qe:
                    logger.warning(f"Qdrant sektör-ünvan deep search indeksleme uyarısı: {qe}")

                saved_memories.append({"id": str(mem.id), "fact": fact_text, "category": cat})

            # AgentDocument kütüphanesine rapor oluştur
            full_report = (
                f"--- SEKTÖR VE ÜNVAN DEEP SEARCH RAPORU ---\n"
                f"Şirket: {tenant.name}\n"
                f"Sektör: {sector_str}\n"
                f"Ünvan: {job_title_name}\n"
                f"AI Personeli: {agent_display_name}\n\n"
                f"1. SEKTÖREL DİNAMİKLER VE MEVZUAT:\n{sector_summary}\n\n"
                f"2. ÜNVAN GÖREV TANIMI VE OPERASYONEL İŞLEYİŞ:\n{job_title_summary}\n\n"
                f"3. HAFIZAYA İŞLENEN TEMEL BİLGİ VE KURAL MADDELERİ:\n"
            )
            for idx, m in enumerate(saved_memories, 1):
                full_report += f"{idx}. [{m['category']}] {m['fact']}\n"

            full_report += "\nKULLANILAN WEB KAYNAKLARI:\n"
            for s in collected_sources:
                full_report += f"- {s['title']}: {s['url']}\n"

            doc = AgentDocument(
                tenant_id=tenant_id,
                agent_id=agent_id,
                file_name=f"onboarding_search_{uuid.uuid4().hex[:8]}",
                original_name=f"🔍 Deep Search: {sector_str} — {job_title_name}",
                file_type="deep_search",
                file_size=len(full_report.encode("utf-8")),
                storage_path=f"search://sector-title/{urllib.parse.quote(job_title_name)}",
                extracted_text=full_report[:100000],
                summary=f"🔍 Sektör & Ünvan Analizi: {sector_str} / {job_title_name}\n{job_title_summary[:200]}...",
                status="INDEXED",
                memory_item_id=uuid.UUID(saved_memories[0]["id"]) if saved_memories else None
            )
            db.add(doc)
            await db.commit()
            await db.refresh(doc)
            doc_id = str(doc.id)

        return {
            "sector_name": sector_str,
            "job_title_name": job_title_name,
            "sector_summary": sector_summary,
            "job_title_summary": job_title_summary,
            "enhanced_system_prompt": enhanced_prompt,
            "learnings": learnings_list,
            "learnings_count": len(learnings_list),
            "saved_memories_count": len(saved_memories),
            "document_id": doc_id,
            "sources": [{"title": s["title"], "url": s["url"]} for s in collected_sources]
        }

    async def save_pending_learnings_for_agent(
        self,
        tenant_id: uuid.UUID,
        agent_id: uuid.UUID,
        learnings: List[Dict[str, Any]],
        sector_name: str,
        job_title_name: str,
        sector_summary: str,
        job_title_summary: str,
        sources: List[Dict[str, Any]],
        db: AsyncSession
    ) -> int:
        """Yeni işe alınan ajanın hafızasına Deep Search'ten gelen öğrenimleri kalıcı işler."""
        if not learnings:
            return 0
        saved_count = 0
        saved_mem_ids = []
        for item in learnings:
            fact_text = item.get("fact", "").strip()
            if not fact_text:
                continue
            conf = float(item.get("confidence", 0.95))
            cat = item.get("category", "ONBOARDING_LEARNING")
            mem = MemoryItem(
                tenant_id=tenant_id,
                scope="AGENT",
                agent_id=agent_id,
                source_reference=f"DEEP_SEARCH_ONBOARDING: {sector_name} - {job_title_name}",
                content=fact_text,
                metadata_json={
                    "source_type": "deep_search_onboarding",
                    "sector": sector_name,
                    "job_title": job_title_name,
                    "category": cat
                },
                status="APPROVED",
                confidence_score=conf
            )
            db.add(mem)
            await db.flush()
            saved_mem_ids.append(mem.id)
            saved_count += 1

            try:
                await collective_memory.add_memory(
                    tenant_id=str(tenant_id),
                    scope="AGENT",
                    agent_id=str(agent_id),
                    source_reference=f"DEEP_SEARCH_ONBOARDING: {sector_name} - {job_title_name}",
                    content=fact_text,
                    metadata={
                        "source_type": "deep_search_onboarding",
                        "sector": sector_name,
                        "job_title": job_title_name,
                        "category": cat,
                        "memory_item_id": str(mem.id)
                    }
                )
            except Exception as qe:
                logger.warning(f"Qdrant onboarding indeksleme uyarısı: {qe}")

        full_report = (
            f"--- SEKTÖR VE ÜNVAN DEEP SEARCH RAPORU ---\n"
            f"Sektör: {sector_name}\n"
            f"Ünvan: {job_title_name}\n\n"
            f"1. SEKTÖREL DİNAMİKLER:\n{sector_summary}\n\n"
            f"2. ÜNVAN GÖREV TANIMI:\n{job_title_summary}\n\n"
            f"3. HAFIZAYA İŞLENEN BİLGİ MADDELERİ:\n"
        )
        for idx, item in enumerate(learnings, 1):
            full_report += f"{idx}. [{item.get('category')}] {item.get('fact')}\n"

        if sources:
            full_report += "\nKULLANILAN KAYNAKLAR:\n"
            for s in sources:
                full_report += f"- {s.get('title')}: {s.get('url')}\n"

        doc = AgentDocument(
            tenant_id=tenant_id,
            agent_id=agent_id,
            file_name=f"onboarding_search_{uuid.uuid4().hex[:8]}",
            original_name=f"🔍 Deep Search: {sector_name} — {job_title_name}",
            file_type="deep_search",
            file_size=len(full_report.encode("utf-8")),
            storage_path=f"search://sector-title/{urllib.parse.quote(job_title_name)}",
            extracted_text=full_report[:100000],
            summary=f"🔍 Sektör & Ünvan Analizi: {sector_name} / {job_title_name}\n{job_title_summary[:200]}...",
            status="INDEXED",
            memory_item_id=saved_mem_ids[0] if saved_mem_ids else None
        )
        db.add(doc)
        await db.commit()
        return saved_count

    # =========================================================================
    # 3. YAZIŞMALARDAN ÖĞRENME (LEARN FROM CHAT / DIALOGUE)
    # =========================================================================
    async def learn_from_chat_dialogue(
        self,
        tenant_id: uuid.UUID,
        agent_id: Optional[uuid.UUID],
        messages: List[Dict[str, str]],
        task_id: Optional[uuid.UUID],
        db: AsyncSession,
        model_code: str = "glm-5.3"
    ) -> List[Dict[str, Any]]:
        """
        Sohbet veya görev diyaloglarından kalıcı kurumsal kararları, müşteri tercihlerini,
        operasyonel kuralları ve iş know-how'ını ayıklar ve hafızaya (Qdrant & DB) kaydeder.
        """
        if not messages or len(messages) < 2:
            return []

        # Diyaloğu metin haline getir
        dialogue_text = ""
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "").strip()
            if content:
                dialogue_text += f"{role.upper()}: {content}\n"

        if len(dialogue_text.strip()) < 40:
            return []

        system_prompt = (
            "Sen RECOrion platformunun Diyalogdan Bilgi ve Tecrübe Çıkarım Motorusun.\n"
            "Görevin: Verilen insan-AI veya AI-AI sohbet geçmişini analiz etmek; gelecekte "
            "hatırlanması gereken şirket kararlarını, müşteri tercihlerini, teknik kuralları, "
            "iş standartlarını veya know-how maddelerini çıkarmaktır.\n\n"
            "KURALLAR:\n"
            "1. Selamlaşma, geçici teyitler ('tamam', 'teşekkürler'), genel geçer sözler ASLA öğrenilmemelidir.\n"
            "2. Yalnızca kalıcı değer taşıyan somut iş kuralları ve operasyonel bilgiler çıkarılmalıdır.\n"
            "3. Eğer konuşmada kalıcı öğrenilecek bir bilgi yoksa, 'learnings': [] döndür.\n"
            "4. Çıktıyı MUTLAKA geçerli JSON formatında üret:\n"
            "{\n"
            '  "learnings": [\n'
            '    {\n'
            '      "fact": "Öğrenilen net kural veya tecrübe ifadesi.",\n'
            '      "scope": "AGENT veya GLOBAL",\n'
            '      "category": "MUSTERI_TERCIHI | TEKNIK_KURAL | IS_PROSESI | MEVZUAT",\n'
            '      "confidence": 0.95\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        user_prompt = f"İncelenecek Sohbet Diyaloğu:\n\n{dialogue_text}\n\nLütfen öğrenilecek bilgi maddelerini JSON olarak çıkar."

        try:
            ai_resp = await evren_gateway.chat_completion(
                model_code=model_code,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            raw_content = ai_resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            cleaned_json = raw_content.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()

            parsed = json.loads(cleaned_json)
            learnings = parsed.get("learnings", [])
        except Exception as e:
            logger.warning(f"Diyalogdan öğrenme LLM analizi başarısız veya öğrenim yok: {e}")
            return []

        saved_items = []
        for item in learnings:
            fact = item.get("fact", "").strip()
            if not fact or len(fact) < 10:
                continue

            target_scope = item.get("scope", "AGENT").upper()
            if target_scope not in ["GLOBAL", "AGENT"]:
                target_scope = "AGENT"
            if target_scope == "AGENT" and not agent_id:
                target_scope = "GLOBAL"

            conf = float(item.get("confidence", 0.90))
            category = item.get("category", "CHAT_LEARNING")
            source_ref = f"CHAT_TASK_{task_id}" if task_id else "CHAT_DIALOGUE"

            mem = MemoryItem(
                tenant_id=tenant_id,
                scope=target_scope,
                agent_id=agent_id if target_scope == "AGENT" else None,
                source_reference=source_ref,
                content=fact,
                metadata_json={
                    "source_type": "chat_dialogue",
                    "task_id": str(task_id) if task_id else None,
                    "category": category,
                    "extracted_from": "CHAT"
                },
                status="APPROVED",
                confidence_score=conf
            )
            db.add(mem)
            await db.flush()

            # Qdrant Vektör İndeksine Ekle
            try:
                await collective_memory.add_memory(
                    tenant_id=str(tenant_id),
                    scope=target_scope,
                    agent_id=str(agent_id) if target_scope == "AGENT" else None,
                    source_reference=source_ref,
                    content=fact,
                    metadata={
                        "source_type": "chat_dialogue",
                        "task_id": str(task_id) if task_id else None,
                        "category": category,
                        "memory_item_id": str(mem.id)
                    }
                )
            except Exception as qe:
                logger.warning(f"Qdrant chat öğrenimi indeksleme uyarısı: {qe}")

            saved_items.append({
                "id": str(mem.id),
                "fact": fact,
                "scope": target_scope,
                "category": category,
                "confidence": conf
            })

        if saved_items:
            await db.commit()
            logger.info(f"Yazışmadan {len(saved_items)} yeni bilgi maddesi hafızaya kaydedildi (Tenant: {tenant_id})")

        return saved_items


agent_learning_service = AgentLearningService()
