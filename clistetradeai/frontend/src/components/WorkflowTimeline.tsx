import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, RadioTower } from "lucide-react";
import type { WorkflowStage } from "../types/market";

interface WorkflowTimelineProps {
  stages: WorkflowStage[];
}

export function WorkflowTimeline({ stages }: WorkflowTimelineProps) {
  const completed = stages.filter((stage) => stage.status === "complete").length;

  return (
    <section className="terminal-card workflow-card">
      <div className="card-header">
        <div>
          <p className="eyebrow">Autonomous Orchestration</p>
          <h2>CrewAI Workflow Transition Map</h2>
        </div>
        <div className="workflow-progress">
          <RadioTower size={16} />
          <span>{completed}/{stages.length} stages</span>
        </div>
      </div>

      <div className="pipeline-track">
        {stages.map((stage, index) => (
          <motion.div
            animate={{ opacity: 1, y: 0 }}
            className={`workflow-node ${stage.status}`}
            initial={{ opacity: 0, y: 12 }}
            key={stage.id}
            transition={{ delay: index * 0.04 }}
          >
            <div className="node-icon">
              <AnimatePresence mode="wait">
                {stage.status === "running" ? (
                  <motion.span
                    animate={{ rotate: 360 }}
                    exit={{ opacity: 0 }}
                    initial={{ opacity: 0 }}
                    key="running"
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <Loader2 size={16} />
                  </motion.span>
                ) : stage.status === "complete" ? (
                  <motion.span exit={{ opacity: 0 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} key="complete">
                    <Check size={16} />
                  </motion.span>
                ) : (
                  <motion.span exit={{ opacity: 0 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} key="pending">
                    {index + 1}
                  </motion.span>
                )}
              </AnimatePresence>
            </div>
            <div>
              <h3>{stage.label}</h3>
              <p>{stage.description}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
