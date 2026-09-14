import { useQuery } from '@tanstack/react-query';
import { getConfig } from '@/lib/api/config';

export function useConfig() {
  return useQuery({ queryKey: ['config'], queryFn: getConfig });
}
