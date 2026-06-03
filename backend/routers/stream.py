"""Streaming SSE endpoints for all operations - sends thinking tokens in real-time."""
from fastapi import APIRouter, Query, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json

from ..core.auth import verify_api_key
from ..core.sse import sse_thinking, sse_result, sse_error, sse_step
from ..core.domain_logic import (
    identify_relevant_norms,
    identify_relevant_norms_multistep,
    develop_amendment_proposals,
    evaluate_proposals,
    deep_evaluate_proposals,
    generate_final_amendment,
    generate_aenderungsbefehle,
    generate_gesetzesentwurf_content,
)
from ..core.models import (
    NormRequest, NormEntry,
    ProposalRequest, ProposalEntry,
    EvaluateRequest, EvaluateEntry,
    DeepEvaluateRequest, DeepEvaluateEntry,
    AmendRequest, AmendEntry,
    AenderungsbefehlRequest,
    GesetzesentwurfRequest,
)
from ..core.xml_parser import extract_section_from_law
from ..core.utils import resolve_law_xml_path
import os

router = APIRouter(prefix="/stream")


def _make_sse_response(generator):
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _make_thinking_callback(queue: asyncio.Queue):
    """Create an on_thinking callback that puts tokens into a queue."""
    async def on_thinking(token: str):
        await queue.put(("thinking", token))
    return on_thinking


async def _stream_task(task: asyncio.Task, queue: asyncio.Queue):
    """Yield SSE events from a queue while a task runs, then yield the result."""
    while not task.done():
        try:
            event_type, payload = await asyncio.wait_for(queue.get(), timeout=0.3)
            if event_type == "thinking":
                yield sse_thinking(payload)
            elif event_type == "step":
                step_index, message = payload
                yield sse_step(step_index, message)
        except asyncio.TimeoutError:
            continue

    # Drain remaining events
    while not queue.empty():
        event_type, payload = await queue.get()
        if event_type == "thinking":
            yield sse_thinking(payload)
        elif event_type == "step":
            step_index, message = payload
            yield sse_step(step_index, message)

    # Return result or error.
    # Wrap string results in a tuple so callers can distinguish them from
    # SSE event strings via isinstance(event, str).
    try:
        result = task.result()
        yield (result,) if isinstance(result, str) else result
    except Exception as e:
        yield sse_error(str(e))


@router.post("/identify")
async def stream_identify(
    request: NormRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(...),
):
    queue: asyncio.Queue = asyncio.Queue()

    async def generate():
        task = asyncio.create_task(
            identify_relevant_norms(
                task_description=request.task_description,
                api_key=api_key,
                model=model,
                selected_laws=request.selected_laws,
                guideline_ids=request.guideline_ids,
                excluded_rule_ids=request.excluded_rule_ids,
                custom_rules=request.custom_rules,
                on_thinking=_make_thinking_callback(queue),
            )
        )

        async for event in _stream_task(task, queue):
            if isinstance(event, str):
                yield event
            else:
                # event is the raw_entries list
                raw_entries = event
                data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
                extracted_sections = {}
                norm_entries = []
                for entry in raw_entries:
                    jurabk = entry["jurabk"]
                    enbez = entry["enbez"]
                    section_key = f"{jurabk}|{enbez}"
                    if section_key in extracted_sections:
                        wording = extracted_sections[section_key]
                    else:
                        xml_file = resolve_law_xml_path(data_dir, jurabk)
                        section_num = enbez.replace("§", "").strip()
                        wording = ""
                        try:
                            wording = extract_section_from_law(xml_file, section_num)
                            extracted_sections[section_key] = wording
                        except Exception:
                            wording = f"Fehler beim Laden des Wortlauts für {jurabk} {enbez}"
                            extracted_sections[section_key] = wording
                    norm_entries.append(NormEntry(jurabk=jurabk, enbez=enbez, P=None, wording=wording))
                yield sse_result({"entries": [e.model_dump() for e in norm_entries]})

    return _make_sse_response(generate())


@router.post("/identify_multistep")
async def stream_identify_multistep(
    request: NormRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(...),
):
    queue: asyncio.Queue = asyncio.Queue()

    async def on_step(step_index: int, message: str):
        await queue.put(("step", (step_index, message)))

    async def generate():
        task = asyncio.create_task(
            identify_relevant_norms_multistep(
                task_description=request.task_description,
                api_key=api_key,
                model=model,
                selected_laws=request.selected_laws,
                guideline_ids=request.guideline_ids,
                excluded_rule_ids=request.excluded_rule_ids,
                custom_rules=request.custom_rules,
                on_step=on_step,
                on_thinking=_make_thinking_callback(queue),
            )
        )

        async for event in _stream_task(task, queue):
            if isinstance(event, str):
                yield event
            else:
                entries_data = [entry.model_dump() for entry in event]
                yield sse_result({"entries": entries_data})

    return _make_sse_response(generate())


@router.post("/generate_proposals")
async def stream_generate_proposals(
    request: ProposalRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(...),
):
    queue: asyncio.Queue = asyncio.Queue()

    async def generate():
        task = asyncio.create_task(
            develop_amendment_proposals(
                task_description=request.task_description,
                relevant_norms=request.relevant_norms,
                api_key=api_key,
                model=model,
                guideline_ids=request.guideline_ids,
                excluded_rule_ids=request.excluded_rule_ids,
                custom_rules=request.custom_rules,
                on_thinking=_make_thinking_callback(queue),
            )
        )

        async for event in _stream_task(task, queue):
            if isinstance(event, str):
                yield event
            else:
                entries = [
                    ProposalEntry(
                        proposalTitle=e.get("proposalTitle", ""),
                        description=e.get("description", ""),
                        affectedNorms=e.get("affectedNorms", []),
                    ).model_dump()
                    for e in event
                ]
                yield sse_result({"entries": entries})

    return _make_sse_response(generate())


@router.post("/evaluate_proposals")
async def stream_evaluate_proposals(
    request: EvaluateRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(...),
):
    queue: asyncio.Queue = asyncio.Queue()

    async def generate():
        task = asyncio.create_task(
            evaluate_proposals(
                task_description=request.task_description,
                relevant_norms=request.relevant_norms,
                amendment_proposals=request.amendment_proposals,
                api_key=api_key,
                model=model,
                guideline_ids=request.guideline_ids,
                excluded_rule_ids=request.excluded_rule_ids,
                custom_rules=request.custom_rules,
                on_thinking=_make_thinking_callback(queue),
            )
        )

        proposal_norms_map = {
            p.proposalTitle: p.affectedNorms
            for p in request.amendment_proposals
        }

        async for event in _stream_task(task, queue):
            if isinstance(event, str):
                yield event
            else:
                entries = [
                    EvaluateEntry(
                        proposalTitle=e.get("proposalTitle", ""),
                        affectedNorms=proposal_norms_map.get(e.get("proposalTitle", ""), []),
                        pro=e.get("pro", []),
                        contra=e.get("contra", []),
                    ).model_dump()
                    for e in event
                ]
                yield sse_result({"entries": entries})

    return _make_sse_response(generate())


@router.post("/deep_evaluate_proposals")
async def stream_deep_evaluate(
    request: DeepEvaluateRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(...),
):
    queue: asyncio.Queue = asyncio.Queue()

    async def generate():
        task = asyncio.create_task(
            deep_evaluate_proposals(
                task_description=request.task_description,
                relevant_norms=request.relevant_norms,
                amendment_proposal=request.amendment_proposal,
                api_key=api_key,
                model=model,
                guideline_ids=request.guideline_ids,
                excluded_rule_ids=request.excluded_rule_ids,
                custom_rules=request.custom_rules,
                on_thinking=_make_thinking_callback(queue),
            )
        )

        async for event in _stream_task(task, queue):
            if isinstance(event, str):
                yield event
            else:
                original_affected_norms = request.amendment_proposal.affectedNorms
                entries = []
                for e in event:
                    entries.append(
                        DeepEvaluateEntry(
                            proposalTitle=e.get("proposalTitle", ""),
                            affectedNorms=original_affected_norms,
                            juristischeBeurteilung=DeepEvaluateEntry.JuristischeBeurteilung(
                                Bewertung=e.get("juristischeBeurteilung", {}).get("Bewertung", ""),
                                PotentielleProbleme=e.get("juristischeBeurteilung", {}).get("PotentielleProbleme", ""),
                                Querverweise=e.get("juristischeBeurteilung", {}).get("Querverweise", []),
                            ),
                            rechtstechnischeBeurteilung=DeepEvaluateEntry.RechtstechnischeBeurteilung(
                                Klarheit=e.get("rechtstechnischeBeurteilung", {}).get("Klarheit", ""),
                                Formulierungsvorschlag=e.get("rechtstechnischeBeurteilung", {}).get("Formulierungsvorschlag", ""),
                                Risikopunkte=e.get("rechtstechnischeBeurteilung", {}).get("Risikopunkte", []),
                            ),
                            dogmatischeBeurteilung=DeepEvaluateEntry.DogmatischeBeurteilung(
                                Systematik=e.get("dogmatischeBeurteilung", {}).get("Systematik", ""),
                                Prinzipien=e.get("dogmatischeBeurteilung", {}).get("Prinzipien", ""),
                            ),
                            folgenabschätzung=DeepEvaluateEntry.Folgenabschätzung(
                                Verwaltungsaufwand=e.get("folgenabschätzung", {}).get("Verwaltungsaufwand", ""),
                                FiskalischeAuswirkungen=e.get("folgenabschätzung", {}).get("FiskalischeAuswirkungen", ""),
                                Praktikabilität=e.get("folgenabschätzung", {}).get("Praktikabilität", ""),
                                Übergangsregelungen=e.get("folgenabschätzung", {}).get("Übergangsregelungen", ""),
                            ),
                            fazitProContra=DeepEvaluateEntry.FazitProContra(
                                Pro=e.get("fazitProContra", {}).get("Pro", []),
                                Contra=e.get("fazitProContra", {}).get("Contra", []),
                                OffeneFragen=e.get("fazitProContra", {}).get("OffeneFragen", []),
                            ),
                        ).model_dump()
                    )
                yield sse_result({"entries": entries})

    return _make_sse_response(generate())


@router.post("/amend")
async def stream_amend(
    request: AmendRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(...),
):
    queue: asyncio.Queue = asyncio.Queue()

    async def generate():
        task = asyncio.create_task(
            generate_final_amendment(
                task_description=request.task_description,
                relevant_norms=request.relevant_norms,
                amendment_proposal=request.amendment_proposal,
                api_key=api_key,
                model=model,
                custom_instructions=request.custom_instructions or None,
                guideline_ids=request.guideline_ids,
                excluded_rule_ids=request.excluded_rule_ids,
                custom_rules=request.custom_rules,
                on_thinking=_make_thinking_callback(queue),
            )
        )

        async for event in _stream_task(task, queue):
            if isinstance(event, str):
                yield event
            else:
                entries = []
                for entry in event:
                    amended_norm = entry.get("amendedNorm", {})
                    entries.append(AmendEntry(
                        originalNorm=NormEntry(
                            jurabk=amended_norm.get("jurabk", ""),
                            enbez=amended_norm.get("enbez"),
                            P=amended_norm.get("P"),
                            wording=amended_norm.get("originalWording", ""),
                        ),
                        amendedNorm=NormEntry(
                            jurabk=amended_norm.get("jurabk", ""),
                            enbez=amended_norm.get("enbez"),
                            P=amended_norm.get("P"),
                            wording=amended_norm.get("amendedWording", ""),
                        ),
                    ).model_dump())
                yield sse_result({"entries": entries})

    return _make_sse_response(generate())


@router.post("/generate_aenderungsbefehle")
async def stream_aenderungsbefehle(
    request: AenderungsbefehlRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(...),
):
    queue: asyncio.Queue = asyncio.Queue()

    async def generate():
        task = asyncio.create_task(
            generate_aenderungsbefehle(
                task_description=request.task_description,
                final_amendments=request.final_amendments,
                api_key=api_key,
                model=model,
                guideline_ids=request.guideline_ids,
                excluded_rule_ids=request.excluded_rule_ids,
                custom_rules=request.custom_rules,
                on_thinking=_make_thinking_callback(queue),
            )
        )

        async for event in _stream_task(task, queue):
            if isinstance(event, str):
                yield event
            else:
                yield sse_result({"response": event[0]})

    return _make_sse_response(generate())


@router.post("/generate_entwurf")
async def stream_entwurf(
    request: GesetzesentwurfRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(...),
):
    queue: asyncio.Queue = asyncio.Queue()

    async def generate():
        task = asyncio.create_task(
            generate_gesetzesentwurf_content(
                task_description=request.task_description,
                aenderungsbefehle=request.aenderungsbefehle,
                api_key=api_key,
                model=model,
                final_amendments=request.final_amendments,
                guideline_ids=request.guideline_ids,
                excluded_rule_ids=request.excluded_rule_ids,
                custom_rules=request.custom_rules,
                on_thinking=_make_thinking_callback(queue),
            )
        )

        async for event in _stream_task(task, queue):
            if isinstance(event, str):
                yield event
            else:
                yield sse_result({"response": event[0]})

    return _make_sse_response(generate())
