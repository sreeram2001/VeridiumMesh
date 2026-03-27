"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Database, ShieldCheck, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  fetchChain,
  fetchChainValidation,
  fetchCredit,
  type ChainResponse,
  type ChainValidationResponse,
  type CreditResponse,
} from "@/lib/api";

export default function ExplorerPage() {
  const [creditId, setCreditId] = useState("");
  const [creditData, setCreditData] = useState<CreditResponse | null>(null);
  const [chainData, setChainData] = useState<ChainResponse | null>(null);
  const [validation, setValidation] = useState<ChainValidationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  async function loadChainMeta() {
    setRefreshing(true);
    setError(null);
    try {
      const [chain, valid] = await Promise.all([fetchChain(), fetchChainValidation()]);
      setChainData(chain);
      setValidation(valid);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load chain data.");
    } finally {
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadChainMeta();
  }, []);

  async function onLookup(e: React.FormEvent) {
    e.preventDefault();
    if (!creditId.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const data = await fetchCredit(creditId.trim());
      setCreditData(data);
    } catch (err) {
      setCreditData(null);
      setError(err instanceof Error ? err.message : "Failed to lookup credit.");
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.16),transparent_35%),linear-gradient(to_bottom,rgba(255,255,255,0.02),transparent_25%)] px-6 py-10 lg:px-10">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-7">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <Link href="/" className="mb-2 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
              <ArrowLeft className="h-4 w-4" /> Back to Home
            </Link>
            <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">Ledger Explorer</h1>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground md:text-base">
              Validate blockchain integrity and inspect any credit ownership state in real time.
            </p>
          </div>
          <Button variant="outline" onClick={loadChainMeta} disabled={refreshing}>
            {refreshing ? "Refreshing..." : "Refresh Chain"}
          </Button>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="border border-border/70 bg-card/65 lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Search className="h-5 w-5 text-primary" /> Credit Lookup
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={onLookup} className="flex flex-col gap-3 sm:flex-row">
                <div className="flex-1 space-y-2">
                  <Label htmlFor="lookup_credit_id">Credit ID</Label>
                  <Input
                    id="lookup_credit_id"
                    placeholder="CRED-XXXXXXXX"
                    value={creditId}
                    onChange={(e) => setCreditId(e.target.value)}
                  />
                </div>
                <div className="sm:self-end">
                  <Button type="submit" disabled={searching} className="w-full sm:w-auto">
                    {searching ? "Searching..." : "Lookup"}
                  </Button>
                </div>
              </form>

              {creditData && (
                <div className="space-y-4 rounded-lg border border-border/60 bg-background/35 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="secondary">{creditData.credit_id}</Badge>
                    <Badge variant={creditData.details.status === "retired" ? "destructive" : "default"}>
                      {creditData.details.status.toUpperCase()}
                    </Badge>
                    <Badge variant="outline">Risk {creditData.details.ai_risk_score.toFixed(4)}</Badge>
                  </div>

                  <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                    <p><span className="text-foreground">Project:</span> {creditData.details.project_type}</p>
                    <p><span className="text-foreground">Vintage:</span> {creditData.details.vintage_year}</p>
                    <p><span className="text-foreground">Tonnes:</span> {creditData.details.tonnes.toLocaleString()}</p>
                  </div>

                  <div>
                    <p className="mb-2 text-sm font-medium">Current Ownership</p>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Owner</TableHead>
                          <TableHead>Units</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {Object.entries(creditData.ownership).map(([owner, units]) => (
                          <TableRow key={owner}>
                            <TableCell>{owner}</TableCell>
                            <TableCell>{units.toLocaleString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border border-border/70 bg-card/65">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <ShieldCheck className="h-5 w-5 text-primary" /> Chain Integrity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="rounded-lg border border-border/60 bg-background/40 p-3">
                <p className="text-muted-foreground">Chain Length</p>
                <p className="text-2xl font-semibold">{validation?.chain_length ?? "-"}</p>
              </div>
              <div className="rounded-lg border border-border/60 bg-background/40 p-3">
                <p className="text-muted-foreground">Status</p>
                <p className="mt-1">
                  {validation ? (
                    <Badge variant={validation.is_valid ? "default" : "destructive"}>
                      {validation.is_valid ? "VALID" : "TAMPERED"}
                    </Badge>
                  ) : (
                    "-"
                  )}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="border border-border/70 bg-card/65">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Database className="h-5 w-5 text-primary" /> Latest Blocks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Index</TableHead>
                  <TableHead>Transactions</TableHead>
                  <TableHead>Previous Hash</TableHead>
                  <TableHead>Hash</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(chainData?.chain ?? [])
                  .slice()
                  .reverse()
                  .slice(0, 8)
                  .map((block) => (
                    <TableRow key={block.hash}>
                      <TableCell>#{block.index}</TableCell>
                      <TableCell>{block.tx_count}</TableCell>
                      <TableCell className="max-w-[220px] truncate">{block.previous_hash}</TableCell>
                      <TableCell className="max-w-[260px] truncate">{block.hash}</TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
