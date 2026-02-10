import { useEffect, useState } from "react";
import { getAgents } from "@/services/agentsService";
import type { Agent } from "@/types/agent";
import { ApiError } from "@/services/httpClient";

interface UseAgentsState {
  data: Agent[] | null;
  isLoading: boolean;
  error: ApiError | null;
}

export function useAgents() {
  const [state, setState] = useState<UseAgentsState>({
    data: null,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    let isSubscribed = true;

    const loadAgents = async () => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const agents = await getAgents();
        if (!isSubscribed) return;
        setState({ data: agents, isLoading: false, error: null });
      } catch (error) {
        if (!isSubscribed) return;
        setState({
          data: null,
          isLoading: false,
          error: error instanceof ApiError ? error : new ApiError({ message: "Failed to load agents" }),
        });
      }
    };

    void loadAgents();

    return () => {
      isSubscribed = false;
    };
  }, []);

  const refetch = () => {
    // trigger effect by resetting state; for now we can call getAgents directly
    setState((prev) => ({ ...prev, isLoading: true }));
    getAgents()
      .then((agents) => {
        setState({ data: agents, isLoading: false, error: null });
      })
      .catch((error) => {
        setState({
          data: null,
          isLoading: false,
          error: error instanceof ApiError ? error : new ApiError({ message: "Failed to load agents" }),
        });
      });
  };

  return {
    ...state,
    refetch,
  };
}


