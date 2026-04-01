import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowUpDown, TrendingUp, TrendingDown, Package, Coins, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { POLLING_INTERVALS } from '@/config/polling';

interface Trade {
  id: string;
  fromResource: string;
  toResource: string;
  fromAmount: number;
  toAmount: number;
  rate: number;
  timestamp: Date;
  traderId?: string;
}

interface Market {
  resource: string;
  price: number;
  volume: number;
  change24h: number;
  available: number;
}

export function ResourceTradingHub({ resources, onResourceUpdate }: any) {
  const [tradeAmount, setTradeAmount] = useState(10);
  const [selectedFrom, setSelectedFrom] = useState('energy');
  const [selectedTo, setSelectedTo] = useState('materials');
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Fetch market data
  const { data: marketData } = useQuery({
    queryKey: ['/api/market'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  // Fetch recent trades
  const { data: recentTrades } = useQuery({
    queryKey: ['/api/trades/recent'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  // Execute trade
  const tradeMutation = useMutation({
    mutationFn: async (trade: { from: string; to: string; amount: number }) => {
      const response = await fetch('/api/trades/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trade)
      });
      if (!response.ok) throw new Error('Trade failed');
      return response.json();
    },
    onSuccess: (data) => {
      toast({
        title: 'Trade Successful',
        description: `Exchanged ${data.fromAmount} ${data.fromResource} for ${data.toAmount} ${data.toResource}`
      });
      queryClient.invalidateQueries({ queryKey: ['/api/colony'] });
      queryClient.invalidateQueries({ queryKey: ['/api/market'] });
    },
    onError: () => {
      toast({
        title: 'Trade Failed',
        description: 'Unable to complete the trade. Check your resources.',
        variant: 'destructive'
      });
    }
  });

  const calculateExchangeRate = (from: string, to: string, amount: number) => {
    // Dynamic exchange rates based on market conditions
    const baseRates: any = {
      energy: { materials: 0.5, food: 2, research: 0.1 },
      materials: { energy: 2, food: 3, research: 0.2 },
      food: { energy: 0.5, materials: 0.33, research: 0.05 },
      research: { energy: 10, materials: 5, food: 20 }
    };

    const rate = baseRates[from]?.[to] || 1;
    const marketAdjustment = Array.isArray(marketData) ? marketData.find((m: Market) => m.resource === to)?.change24h || 0 : 0;
    const adjustedRate = rate * (1 + marketAdjustment / 100);
    
    return Math.round(amount * adjustedRate * 100) / 100;
  };

  const canAffordTrade = () => {
    return (resources[selectedFrom] || 0) >= tradeAmount;
  };

  return (
    <div className="space-y-6">
      <Card className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-blue-500/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Coins className="w-5 h-5 text-yellow-400" />
            Resource Trading Hub
          </CardTitle>
          <CardDescription>Exchange resources with dynamic market rates</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="trade" className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="trade">Trade</TabsTrigger>
              <TabsTrigger value="market">Market</TabsTrigger>
              <TabsTrigger value="history">History</TabsTrigger>
            </TabsList>

            <TabsContent value="trade" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="from-resource">From Resource</Label>
                  <select
                    id="from-resource"
                    value={selectedFrom}
                    onChange={(e) => setSelectedFrom(e.target.value)}
                    className="w-full px-3 py-2 bg-black/50 border border-gray-600 rounded text-white"
                  >
                    <option value="energy">Energy ({resources.energy || 0})</option>
                    <option value="materials">Materials ({resources.materials || 0})</option>
                    <option value="food">Food ({resources.food || 0})</option>
                    <option value="research">Research ({resources.research || 0})</option>
                  </select>
                </div>

                <div className="flex items-center justify-center">
                  <ArrowUpDown className="w-8 h-8 text-blue-400" />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="to-resource">To Resource</Label>
                  <select
                    id="to-resource"
                    value={selectedTo}
                    onChange={(e) => setSelectedTo(e.target.value)}
                    className="w-full px-3 py-2 bg-black/50 border border-gray-600 rounded text-white"
                  >
                    <option value="energy">Energy</option>
                    <option value="materials">Materials</option>
                    <option value="food">Food</option>
                    <option value="research">Research</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="amount">Amount to Trade</Label>
                <Input
                  id="amount"
                  type="number"
                  value={tradeAmount}
                  onChange={(e) => setTradeAmount(Number(e.target.value))}
                  min="1"
                  max={resources[selectedFrom] || 0}
                  className="bg-black/50 border-gray-600"
                />
              </div>

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="p-4 bg-black/30 rounded border border-blue-500/20"
              >
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Exchange Rate:</span>
                  <span className="text-xl font-bold text-green-400">
                    {tradeAmount} {selectedFrom} → {calculateExchangeRate(selectedFrom, selectedTo, tradeAmount)} {selectedTo}
                  </span>
                </div>
              </motion.div>

              <Button
                onClick={() => tradeMutation.mutate({
                  from: selectedFrom,
                  to: selectedTo,
                  amount: tradeAmount
                })}
                disabled={!canAffordTrade() || tradeMutation.isPending}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500"
              >
                {tradeMutation.isPending ? 'Processing...' : 'Execute Trade'}
              </Button>
            </TabsContent>

            <TabsContent value="market" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Array.isArray(marketData) ? marketData.map((market: Market) => (
                  <motion.div
                    key={market.resource}
                    whileHover={{ scale: 1.02 }}
                    className="p-4 bg-black/30 rounded border border-gray-700"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-medium text-white capitalize">{market.resource}</h4>
                        <p className="text-2xl font-bold text-yellow-400">{market.price.toFixed(2)}</p>
                      </div>
                      <div className={`flex items-center gap-1 ${market.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {market.change24h >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        <span>{Math.abs(market.change24h).toFixed(1)}%</span>
                      </div>
                    </div>
                    <div className="flex justify-between text-sm text-gray-400">
                      <span>Volume: {market.volume}</span>
                      <span>Available: {market.available}</span>
                    </div>
                  </motion.div>
                )) : <div className="col-span-2 text-center text-gray-400 py-8">Loading market data...</div>}
              </div>
            </TabsContent>

            <TabsContent value="history" className="space-y-2">
              <div className="max-h-64 overflow-y-auto space-y-2">
                {Array.isArray(recentTrades) ? recentTrades.map((trade: Trade) => (
                  <motion.div
                    key={trade.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="p-3 bg-black/20 rounded border border-gray-700"
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <Package className="w-4 h-4 text-blue-400" />
                        <span className="text-sm text-gray-300">
                          {trade.fromAmount} {trade.fromResource} → {trade.toAmount} {trade.toResource}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(trade.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </motion.div>
                )) : <div className="text-center text-gray-400 py-8">No recent trades</div>}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Multiplayer Trading */}
      <Card className="bg-gradient-to-br from-green-900/20 to-blue-900/20 border-green-500/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5 text-green-400" />
            Multiplayer Trading
          </CardTitle>
          <CardDescription>Trade with other colonies in real-time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-400">
            <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Connect to multiplayer session to enable player trading</p>
            <Button variant="outline" className="mt-4">
              Join Trading Network
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
