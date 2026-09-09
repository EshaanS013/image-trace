import { useQuery } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { Empty, ErrorState, Loading, formatDate } from "../components";

export function CustodyPage(){const {caseId=""}=useParams();const query=useQuery({queryKey:["custody",caseId],queryFn:()=>api.custody(caseId)});return <div className="workspace"><div className="workspace-heading"><div><p className="eyebrow">AUDIT HISTORY</p><h1>Chain of custody</h1><p>Append-only acquisition, verification, review, note, and reporting events.</p></div></div>{query.isLoading?<Loading/>:query.error?<ErrorState message={query.error.message}/>:!query.data?.length?<Empty title="No custody events" body="Events will be recorded as evidence is acquired and reviewed."/>:<div className="audit-list">{query.data.map(event=><article key={event.id}><div className="audit-icon"><ShieldCheck size={17}/></div><div><strong>{event.event_type.replaceAll("_"," ")}</strong><p>{event.actor} · {event.evidence_file_id?`Evidence ${event.evidence_file_id.slice(0,8)}`:"Case event"}</p><details><summary>Technical details</summary><pre>{JSON.stringify(JSON.parse(event.details_json),null,2)}</pre></details></div><time>{formatDate(event.timestamp)}</time></article>)}</div>}</div>}

