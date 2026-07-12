import {
  useCallback,
  useEffect,
  useState,
} from "react";

export type PipelineStage =
  | "New"
  | "Contacted"
  | "Demo"
  | "Proposal"
  | "Closing"
  | "Won"
  | "Lost";

export type PipelineState = {
  stage: PipelineStage;
  dealValue: number;
  nextAction: string;
};

export type PipelineMap = Record<
  string,
  PipelineState
>;

type RemoteDeal = {
  lead_id?: unknown;
  stage?: unknown;
  deal_value?: unknown;
  next_action?: unknown;
};

type UnifiedPipelineEventDetail = {
  pipeline: PipelineMap;
};

const API_BASE = String(
  import.meta.env.VITE_BACKEND_URL ||
    "http://127.0.0.1:5000"
).replace(/\/+$/, "");

export const PIPELINE_STORAGE_KEY =
  "wolf-os-buyer-pipeline-v2";

export const PIPELINE_STATE_EVENT =
  "wolf-os-unified-pipeline-updated";

export const PIPELINE_ACTIVITY_EVENT =
  "wolf-os-pipeline-activity-updated";

const stages: PipelineStage[] = [
  "New",
  "Contacted",
  "Demo",
  "Proposal",
  "Closing",
  "Won",
  "Lost",
];

function resolveOwnerToken(
  ownerToken = ""
) {
  return (
    ownerToken ||
    window.localStorage.getItem(
      "wolf_owner_token"
    ) ||
    ""
  );
}

function isStage(
  value: unknown
): value is PipelineStage {
  return (
    typeof value === "string" &&
    stages.includes(
      value as PipelineStage
    )
  );
}

function normalizePipeline(
  rows: unknown
): PipelineMap {
  const pipeline: PipelineMap = {};

  if (!Array.isArray(rows)) {
    return pipeline;
  }

  for (const raw of rows) {
    if (
      typeof raw !== "object" ||
      raw === null
    ) {
      continue;
    }

    const row =
      raw as RemoteDeal;

    const leadId = String(
      row.lead_id || ""
    ).trim();

    if (!leadId) {
      continue;
    }

    pipeline[leadId] = {
      stage: isStage(row.stage)
        ? row.stage
        : "New",
      dealValue: Math.max(
        0,
        Number(row.deal_value) || 0
      ),
      nextAction: String(
        row.next_action || ""
      ),
    };
  }

  return pipeline;
}

export function readPipelineCache():
  PipelineMap {
  try {
    const raw =
      window.localStorage.getItem(
        PIPELINE_STORAGE_KEY
      );

    if (!raw) {
      return {};
    }

    return JSON.parse(
      raw
    ) as PipelineMap;

  } catch {
    return {};
  }
}

function publishPipeline(
  pipeline: PipelineMap
) {
  window.localStorage.setItem(
    PIPELINE_STORAGE_KEY,
    JSON.stringify(pipeline)
  );

  window.dispatchEvent(
    new CustomEvent<UnifiedPipelineEventDetail>(
      PIPELINE_STATE_EVENT,
      {
        detail: {
          pipeline,
        },
      }
    )
  );
}

export async function fetchUnifiedPipeline(
  ownerToken = ""
): Promise<PipelineMap> {
  const token =
    resolveOwnerToken(ownerToken);

  if (!token) {
    throw new Error(
      "Owner token is not available."
    );
  }

  const response = await fetch(
    `${API_BASE}/api/owner/pipeline-state`,
    {
      headers: {
        Authorization:
          `Bearer ${token}`,
      },
    }
  );

  const payload =
    await response.json();

  if (
    !response.ok ||
    !payload?.ok
  ) {
    throw new Error(
      payload?.error ||
        `Pipeline load failed: ${response.status}`
    );
  }

  const pipeline =
    normalizePipeline(
      payload.pipeline_deals
    );

  publishPipeline(pipeline);

  return pipeline;
}

export async function saveUnifiedPipelineDeal(
  leadId: string,
  deal: PipelineState,
  ownerToken = ""
): Promise<PipelineMap> {
  const token =
    resolveOwnerToken(ownerToken);

  if (!token) {
    throw new Error(
      "Owner token is not available."
    );
  }

  const response = await fetch(
    `${API_BASE}/api/owner/pipeline-state/${encodeURIComponent(
      leadId
    )}`,
    {
      method: "PUT",
      headers: {
        Authorization:
          `Bearer ${token}`,
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        stage: deal.stage,
        deal_value:
          deal.dealValue,
        next_action:
          deal.nextAction,
      }),
    }
  );

  const payload =
    await response.json();

  if (
    !response.ok ||
    !payload?.ok
  ) {
    throw new Error(
      payload?.error ||
        `Pipeline save failed: ${response.status}`
    );
  }

  const pipeline =
    normalizePipeline(
      payload.pipeline_deals
    );

  publishPipeline(pipeline);

  window.dispatchEvent(
    new CustomEvent(
      PIPELINE_ACTIVITY_EVENT
    )
  );

  return pipeline;
}

export function useUnifiedPipeline(
  ownerToken = ""
) {
  const [pipeline, setPipeline] =
    useState<PipelineMap>(
      readPipelineCache
    );

  const [
    pipelineStatus,
    setPipelineStatus,
  ] = useState(
    "Connecting to unified SQLite pipeline..."
  );

  const [
    pipelineReady,
    setPipelineReady,
  ] = useState(false);

  const refreshPipeline =
    useCallback(async () => {
      try {
        const next =
          await fetchUnifiedPipeline(
            ownerToken
          );

        setPipeline(next);

        setPipelineReady(true);

        setPipelineStatus(
          `${Object.keys(next).length} deals synchronized from SQLite.`
        );

        return next;

      } catch (error) {
        setPipelineReady(false);

        setPipelineStatus(
          error instanceof Error
            ? `Pipeline sync error: ${error.message}`
            : "Pipeline synchronization failed."
        );

        throw error;
      }
    }, [ownerToken]);

  useEffect(() => {
    const onPipelineUpdate = (
      event: Event
    ) => {
      const detail = (
        event as CustomEvent<
          UnifiedPipelineEventDetail
        >
      ).detail;

      if (detail?.pipeline) {
        setPipeline(
          detail.pipeline
        );

        setPipelineReady(true);

        setPipelineStatus(
          `${Object.keys(detail.pipeline).length} deals synchronized from SQLite.`
        );

        return;
      }

      setPipeline(
        readPipelineCache()
      );
    };

    const onStorage = (
      event: StorageEvent
    ) => {
      if (
        event.key ===
        PIPELINE_STORAGE_KEY
      ) {
        setPipeline(
          readPipelineCache()
        );
      }
    };

    window.addEventListener(
      PIPELINE_STATE_EVENT,
      onPipelineUpdate
    );

    window.addEventListener(
      "storage",
      onStorage
    );

    void refreshPipeline().catch(
      () => {
        return;
      }
    );

    return () => {
      window.removeEventListener(
        PIPELINE_STATE_EVENT,
        onPipelineUpdate
      );

      window.removeEventListener(
        "storage",
        onStorage
      );
    };
  }, [refreshPipeline]);

  return {
    pipeline,
    pipelineReady,
    pipelineStatus,
    refreshPipeline,
  };
}
