import { useEffect, useMemo, useRef, useState } from 'react';
import { createCloudinary, cloudName as envCloudName } from '../cloudinary/config';
import { ApiError, fetchHealth, fetchItems, fetchStats } from '../api/client';
import type { Cloudinary } from '@cloudinary/url-gen';
import type { HealthResponse, ItemPage, ItemQuery, WardrobeStats } from '../types';

const PAGE_SIZE = 12;

export const defaultQuery = (): ItemQuery => ({
  q: '',
  category: '',
  colour: '',
  pattern: '',
  style: '',
  occasion: '',
  sort: 'recent',
  page: 1,
  pageSize: PAGE_SIZE,
});

export function useWardrobe() {
  const [query, setQuery] = useState<ItemQuery>(defaultQuery);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [pageData, setPageData] = useState<ItemPage | null>(null);
  const [stats, setStats] = useState<WardrobeStats | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [highlightId, setHighlightId] = useState<number | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);
  const requestId = useRef(0);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  const requestQuery = useMemo(
    () => ({ ...query, q: debouncedSearch }),
    [query, debouncedSearch],
  );

  useEffect(() => {
    const currentRequest = ++requestId.current;
    const pending = Promise.all([
      fetchHealth(),
      fetchItems(requestQuery),
      fetchStats(),
    ]);
    pending
      .then(([healthResponse, itemsResponse, statsResponse]) => {
        if (currentRequest !== requestId.current) return;
        setHealth(healthResponse);
        setPageData(itemsResponse);
        setStats(statsResponse);
        setError(null);
      })
      .catch((err: unknown) => {
        if (currentRequest !== requestId.current) return;
        setError(err instanceof ApiError ? err.message : 'The wardrobe could not be loaded.');
      })
      .finally(() => {
        if (currentRequest === requestId.current) setLoading(false);
      });
  }, [requestQuery, refreshToken]);

  useEffect(() => {
    if (!highlightId) return;
    const timer = window.setTimeout(() => setHighlightId(null), 4000);
    return () => window.clearTimeout(timer);
  }, [highlightId]);

  const resolvedCloudName = health?.cloud_name || envCloudName || '';
  const cld: Cloudinary | null = useMemo(
    () => (resolvedCloudName ? createCloudinary(resolvedCloudName) : null),
    [resolvedCloudName],
  );

  function updateQuery(patch: Partial<ItemQuery>) {
    setLoading(true);
    setQuery((current) => ({ ...current, ...patch }));
  }

  function updateSearch(value: string) {
    setSearch(value);
    setQuery((current) => (current.page === 1 ? current : { ...current, page: 1 }));
  }

  function clearFilters() {
    setLoading(true);
    setSearch('');
    setDebouncedSearch('');
    setQuery((current) => ({
      ...defaultQuery(),
      sort: current.sort,
    }));
  }

  function showNewest(itemId: number) {
    setLoading(true);
    setSearch('');
    setDebouncedSearch('');
    setQuery(defaultQuery());
    setHighlightId(itemId);
    setRefreshToken((value) => value + 1);
  }

  function refresh() {
    setLoading(true);
    setRefreshToken((value) => value + 1);
  }

  return {
    cld,
    health,
    query,
    search,
    pageData,
    stats,
    loading,
    error,
    highlightId,
    updateQuery,
    updateSearch,
    clearFilters,
    showNewest,
    refresh,
  };
}
