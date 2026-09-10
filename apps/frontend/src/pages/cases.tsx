import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  FolderPlus,
  Moon,
  ShieldCheck,
  Sun,
  Trash2,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import {
  Button,
  Empty,
  ErrorState,
  Field,
  Loading,
  Modal,
  Status,
  formatDate,
} from "../components";
import { useWorkspace } from "../state";
import type { Case } from "../types";

function PublicHeader() {
  const { theme, toggleTheme } = useWorkspace();
  return (
    <header className="public-header">
      <Link className="brand" to="/cases">
        <div className="brand-mark">IT</div>
        <div>
          <strong>IMAGE TRACE</strong>
          <span>Local investigation workspace</span>
        </div>
      </Link>
      <button
        className="icon-button"
        onClick={toggleTheme}
        aria-label="Toggle theme"
      >
        {theme === "dark" ? <Sun /> : <Moon />}
      </button>
    </header>
  );
}
export function CaseListPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["cases"],
    queryFn: api.cases,
  });
  const [pending, setPending] = useState<Case | null>(null);
  const remove = useMutation({
    mutationFn: () => api.deleteCase(pending!.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      setPending(null);
    },
  });
  return (
    <div className="public-page">
      <PublicHeader />
      <div className="page-wrap">
        <div className="page-heading">
          <div>
            <p className="eyebrow">CASE REGISTRY</p>
            <h1>Your investigations</h1>
            <p>
              Open a workspace or register a new consented evidence collection.
            </p>
          </div>
          <Button
            icon={FolderPlus}
            onClick={() => location.assign("/cases/new")}
          >
            New case
          </Button>
        </div>
        {isLoading ? (
          <Loading />
        ) : error ? (
          <ErrorState message={(error as Error).message} />
        ) : data?.items.length ? (
          <div className="case-grid">
            {data.items.map((item) => (
              <article className="case-card" key={item.id}>
                <Link
                  className="case-card-link"
                  to={`/cases/${item.id}/overview`}
                >
                  <div className="case-card-head">
                    <span>{item.case_number}</span>
                    <Status value={item.status} />
                  </div>
                  <h2>{item.name}</h2>
                  <p>{item.description || "No case description provided."}</p>
                  <div className="case-card-foot">
                    <span>
                      {item.analyst_name} · Updated{" "}
                      {formatDate(item.updated_at)}
                    </span>
                    <ArrowRight size={18} />
                  </div>
                </Link>
                <button
                  className="case-delete-button"
                  onClick={() => setPending(item)}
                >
                  <Trash2 size={15} />
                  Delete case
                </button>
              </article>
            ))}
          </div>
        ) : (
          <Empty
            title="No cases yet"
            body="Create a case to begin preserving and reviewing synthetic or consented image evidence."
            action={
              <Link className="button primary" to="/cases/new">
                <FolderPlus size={16} />
                Create first case
              </Link>
            }
          />
        )}
      </div>
      <Modal
        open={!!pending}
        onOpenChange={(open) => {
          if (!open && !remove.isPending) setPending(null);
        }}
        title={`Delete ${pending?.case_number ?? "case"}?`}
        description="This permanently removes the case, its evidence files, reports, findings, and custody history from local storage."
      >
        <div className="dialog-actions">
          <Button
            variant="secondary"
            disabled={remove.isPending}
            onClick={() => setPending(null)}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            disabled={remove.isPending}
            onClick={() => remove.mutate()}
            icon={Trash2}
          >
            {remove.isPending ? "Deleting…" : "Delete permanently"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
export function NewCasePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    case_number: "",
    name: "",
    description: "",
    analyst_name: "",
    case_timezone: "",
  });
  const mutation = useMutation({
    mutationFn: () =>
      api.createCase({ ...form, case_timezone: form.case_timezone || null }),
    onSuccess: (item) => navigate(`/cases/${item.id}/overview`),
  });
  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };
  return (
    <div className="public-page">
      <PublicHeader />
      <div className="form-wrap">
        <Link className="back-link" to="/cases">
          ← Back to cases
        </Link>
        <p className="eyebrow">NEW CASE</p>
        <h1>Register an investigation</h1>
        <p>
          Start with scope and analyst context. Evidence can be added after the
          case is created.
        </p>
        <form className="case-form" onSubmit={submit}>
          <div className="form-grid">
            <Field label="Case number">
              <input
                required
                maxLength={80}
                value={form.case_number}
                onChange={(e) =>
                  setForm({ ...form, case_number: e.target.value })
                }
                placeholder="CASE-2026-001"
              />
            </Field>
            <Field label="Analyst">
              <input
                required
                maxLength={160}
                value={form.analyst_name}
                onChange={(e) =>
                  setForm({ ...form, analyst_name: e.target.value })
                }
                placeholder="Analyst name"
              />
            </Field>
          </div>
          <Field label="Case name">
            <input
              required
              maxLength={200}
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Synthetic route review"
            />
          </Field>
          <Field label="Description">
            <textarea
              maxLength={5000}
              rows={4}
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              placeholder="Scope, evidence source, and consent context"
            />
          </Field>
          <Field
            label="Timezone assumption (optional)"
            hint="Use an IANA name such as Asia/Kolkata. Leave blank to preserve naive timestamps as local/unknown."
          >
            <input
              value={form.case_timezone}
              onChange={(e) =>
                setForm({ ...form, case_timezone: e.target.value })
              }
              placeholder="Asia/Kolkata"
            />
          </Field>
          {mutation.error && <ErrorState message={mutation.error.message} />}
          <div className="form-actions">
            <Link className="button secondary" to="/cases">
              Cancel
            </Link>
            <Button
              type="submit"
              disabled={mutation.isPending}
              icon={ShieldCheck}
            >
              {mutation.isPending ? "Creating…" : "Create case"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
