import { useEffect, useMemo, useRef, useState } from "react";
import { startAnalysis, pollWorkflow, fetchResult, initialWorkflow } from "../services/marketApi";
import type { MarketAnalysisResult, MarketRequest, WorkflowStage } from "../types/market";

const POLL_INTERVAL_MS = 400;

export function useMarketAnalysis() {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<MarketAnalysisResult | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowStage[]>(initialWorkflow());
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const cancelledRef = useRef(false);

  const activeStage = useMemo(
    () => workflow.find((stage) => stage.status === "running")?.id ?? null,
    [workflow]
  );

  useEffect(() => {
    return () => {
      cancelledRef.current = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  async function runAnalysis(request: MarketRequest) {
    cancelledRef.current = false;
    setIsRunning(true);
    setError(null);
    setResult(null);
    setWorkflow(initialWorkflow());

    try {
      const { requestId, workflow: initial } = await startAnalysis(request);
      if (cancelledRef.current) return;

      setWorkflow(initial);

      await pollUntilComplete(requestId);
    } catch (analysisError) {
      if (!cancelledRef.current) {
        const message = analysisError instanceof Error ? analysisError.message : "Market analysis failed";
        setError(message);
        setWorkflow((current) => current.map((stage) => ({ ...stage, status: "error" })));
      }
    } finally {
      if (!cancelledRef.current) {
        setIsRunning(false);
      }
    }
  }

  async function pollUntilComplete(requestId: string) {
    return new Promise<void>((resolve, reject) => {
      pollRef.current = setInterval(async () => {
        try {
          const status = await pollWorkflow(requestId);
          if (cancelledRef.current) {
            clearInterval(pollRef.current!);
            reject(new Error("Cancelled"));
            return;
          }

          setWorkflow(status.workflow);

          if (status.error) {
            clearInterval(pollRef.current!);
            setError(status.error);
            setWorkflow((current) => current.map((stage) => ({ ...stage, status: "error" })));
            reject(new Error(status.error));
            return;
          }

          if (status.complete) {
            clearInterval(pollRef.current!);

            try {
              const fullResult = await fetchResult(requestId);
              if (!cancelledRef.current) {
                setResult(fullResult);
                setWorkflow(fullResult.workflow);
              }
              resolve();
            } catch (fetchError) {
              reject(fetchError);
            }
          }
        } catch {
          // Transient poll errors are ignored; next tick will retry
        }
      }, POLL_INTERVAL_MS);
    });
  }

  return {
    activeStage,
    isRunning,
    error,
    result,
    workflow,
    runAnalysis
  };
}
