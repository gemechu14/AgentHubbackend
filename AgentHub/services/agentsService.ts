import { apiFetch } from "./httpClient";
import type { Agent } from "@/types/agent";
import type { ApiListResponse } from "@/types/api";

export async function getAgents(): Promise<Agent[]> {
  const response = await apiFetch<ApiListResponse<Agent>>("/agents");
  return response.data;
}


