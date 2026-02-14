/**
 * Shared hook for URL-driven search flows (Explore and Compare).
 * Keeps params in sync with URL; replaceState on draft updates, pushState on submit;
 * fetches when URL has valid params (initial load or popstate).
 */

import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";

export interface UseUrlDrivenSearchOptions<TParams, TResult> {
  parse: (searchParams: URLSearchParams) => { params: TParams; validationError: string | null };
  build: (params: TParams) => URLSearchParams;
  canFetch: (params: TParams) => boolean;
  fetch: (params: TParams) => Promise<TResult>;
  /** Message to show when user submits but canFetch is false (e.g. empty location). */
  emptyFetchMessage?: string;
  /** Normalize params before submit (e.g. trim query strings). Used for fetch and pushState. */
  trimParams?: (params: TParams) => TParams;
}

export interface UseUrlDrivenSearchResult<TParams, TResult> {
  params: TParams;
  result: TResult | null;
  loading: boolean;
  error: string | null;
  validationMessage: string | null;
  updateDraft: (params: TParams) => void;
  submit: () => Promise<void>;
}

/**
 * Generic hook for a page that drives search from URL (q/radius or a/b/radius).
 * - params: current parsed params (form binds to this).
 * - updateDraft: call when user edits form (replaceState, no fetch).
 * - submit: validate, fetch, then pushState.
 * - Effect: when searchParams change, sync params and validationMessage; if valid and canFetch, run fetch.
 */
export function useUrlDrivenSearch<TParams, TResult>(
  options: UseUrlDrivenSearchOptions<TParams, TResult>
): UseUrlDrivenSearchResult<TParams, TResult> {
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const [searchParams, setSearchParams] = useSearchParams();
  const initial = optionsRef.current.parse(searchParams);
  const [params, setParams] = useState<TParams>(initial.params);
  const [result, setResult] = useState<TResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationMessage, setValidationMessage] = useState<string | null>(initial.validationError);
  const weJustSetParamsRef = useRef(false);
  /** Tracks submit version so stale async work does not update state. */
  const submitVersionRef = useRef(0);

  useEffect(() => {
    if (weJustSetParamsRef.current) {
      weJustSetParamsRef.current = false;
      return;
    }
    const { parse, canFetch, fetch: doFetch } = optionsRef.current;
    const { params: nextParams, validationError } = parse(searchParams);
    setParams(nextParams);
    setValidationMessage(validationError);
    submitVersionRef.current += 1;
    if (validationError || !canFetch(nextParams)) {
      setResult(null);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setError(null);
    setLoading(true);
    doFetch(nextParams)
      .then((data) => {
        if (!cancelled) setResult(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Request failed");
          setResult(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  function updateDraft(next: TParams) {
    weJustSetParamsRef.current = true;
    const built = optionsRef.current.build(next);
    const { validationError } = optionsRef.current.parse(built);
    setParams(next);
    setValidationMessage(validationError);
    setSearchParams(built, { replace: true });
  }

  async function submit() {
    const { parse, build, canFetch, fetch: doFetch, emptyFetchMessage, trimParams } = optionsRef.current;
    const toSubmit = trimParams ? trimParams(params) : params;
    const { validationError } = parse(build(toSubmit));
    if (validationError) {
      setValidationMessage(validationError);
      return;
    }
    if (!canFetch(toSubmit)) {
      setValidationMessage(emptyFetchMessage ?? null);
      return;
    }
    setValidationMessage(null);
    setError(null);
    setLoading(true);
    const version = ++submitVersionRef.current;
    try {
      const data = await doFetch(toSubmit);
      if (submitVersionRef.current !== version) return;
      setResult(data);
      weJustSetParamsRef.current = true;
      setParams(toSubmit);
      setSearchParams(build(toSubmit), { replace: false });
    } catch (err) {
      if (submitVersionRef.current !== version) return;
      setError(err instanceof Error ? err.message : "Request failed");
      setResult(null);
    } finally {
      if (submitVersionRef.current === version) setLoading(false);
    }
  }

  return {
    params,
    result,
    loading,
    error,
    validationMessage,
    updateDraft,
    submit,
  };
}
