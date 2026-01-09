import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { debateApi } from '@/api';
import { useUIStore } from '@/stores';

export const useDebates = () => {
  const queryClient = useQueryClient();
  const { addNotification } = useUIStore();

  const {
    data: debates,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['debates'],
    queryFn: () => debateApi.listDebates(),
    refetchInterval: 10000, // Poll every 10s
  });

  const createDebateMutation = useMutation({
    mutationFn: debateApi.createDebate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['debates'] });
      addNotification({
        title: 'Debate Created',
        message: 'Your debate is starting...',
        type: 'success',
      });
    },
    onError: (error: Error) => {
      addNotification({
        title: 'Error',
        message: error.message || 'Failed to create debate',
        type: 'error',
      });
    },
  });

  const deleteDebateMutation = useMutation({
    mutationFn: debateApi.deleteDebate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['debates'] });
      addNotification({
        title: 'Deleted',
        message: 'Debate has been deleted',
        type: 'info',
      });
    },
    onError: (error: Error) => {
      addNotification({
        title: 'Error',
        message: error.message || 'Failed to delete debate',
        type: 'error',
      });
    },
  });

  const stopDebateMutation = useMutation({
    mutationFn: debateApi.stopDebate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['debates'] });
      addNotification({
        title: 'Stopped',
        message: 'Debate has been stopped',
        type: 'warning',
      });
    },
  });

  return {
    debates,
    isLoading,
    error,
    refetch,
    createDebate: createDebateMutation.mutate,
    isCreating: createDebateMutation.isPending,
    deleteDebate: deleteDebateMutation.mutate,
    isDeleting: deleteDebateMutation.isPending,
    stopDebate: stopDebateMutation.mutate,
    isStopping: stopDebateMutation.isPending,
  };
};

export const useDebate = (debateId: string) => {
  const { data: debate, isLoading, error, refetch } = useQuery({
    queryKey: ['debate', debateId],
    queryFn: () => debateApi.getDebate(debateId),
    enabled: !!debateId,
    refetchInterval: (query) => {
      // Refetch every 2s if debate is running
      if (query.state.data?.status === 'running' || query.state.data?.status === 'pending') {
        return 2000;
      }
      return false;
    },
  });

  return { debate, isLoading, error, refetch };
};

export const useAdapters = () => {
  const { data: adapters, isLoading } = useQuery({
    queryKey: ['adapters'],
    queryFn: () => debateApi.listAdapters(),
    staleTime: 60000, // Cache for 1 minute
  });

  return { adapters, isLoading };
};

export const useHealthCheck = () => {
  const { data: health, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: () => debateApi.healthCheck(),
    refetchInterval: 30000, // Check every 30s
  });

  return { health, isLoading, error, isHealthy: health?.status === 'healthy' };
};
