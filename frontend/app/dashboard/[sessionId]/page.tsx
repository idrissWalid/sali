"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { 
  BarChart, Bar, PieChart, Pie, LineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell 
} from "recharts";
import { ArrowLeft, Loader2, Table2, BarChart3, Info } from "lucide-react";

// Colors for charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#d0ed57', '#a4de6c'];

export default function DashboardPage() {
  const { sessionId } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedVar, setSelectedVar] = useState<string>("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${apiUrl}/api/dashboard/data/${sessionId}`);
        if (!res.ok) throw new Error("Erreur lors de la récupération des données");
        const json = await res.json();
        setData(json);
        
        // Select first variable by default if distributions exist
        const vars = Object.keys(json.distributions || {});
        if (vars.length > 0) {
          setSelectedVar(vars[0]);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    if (sessionId) fetchData();
  }, [sessionId]);

  if (loading) return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-50 dark:bg-[#111]">
      <Loader2 className="animate-spin w-8 h-8 text-blue-500" />
      <span className="ml-3 text-lg font-medium text-gray-700 dark:text-gray-300">Chargement du dashboard...</span>
    </div>
  );

  if (error) return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-50 dark:bg-[#111]">
      <div className="bg-red-50 text-red-600 p-6 rounded-xl border border-red-200">
        <h2 className="text-xl font-bold mb-2">Erreur</h2>
        <p>{error}</p>
      </div>
    </div>
  );

  if (!data) return null;

  const { overview, preview, variables, distributions, filename } = data;
  const activeDist = selectedVar ? distributions[selectedVar] : null;

  return (
    <div className="min-h-screen w-full bg-gray-50 dark:bg-[#111] text-gray-900 dark:text-gray-100 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard Analytique</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-2">
              <Table2 className="w-4 h-4" /> Fichier source : <span className="font-semibold text-gray-700 dark:text-gray-300">{filename}</span>
            </p>
          </div>
          <button onClick={() => window.close()} className="px-4 py-2 bg-white dark:bg-[#222] border border-gray-200 dark:border-gray-800 rounded-lg shadow-sm hover:bg-gray-50 dark:hover:bg-[#333] transition flex items-center gap-2 text-sm font-medium">
            <ArrowLeft className="w-4 h-4" /> Fermer l'onglet
          </button>
        </div>

        {/* Global Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard title="Lignes" value={overview.n_lignes?.toLocaleString()} icon="📊" />
          <StatCard title="Colonnes" value={overview.n_colonnes?.toLocaleString()} icon="📑" />
          <StatCard title="Valeurs manquantes" value={`${overview.pct_valeurs_manquantes_total || 0}%`} icon="⚠️" />
          <StatCard title="Doublons" value={overview.n_doublons?.toLocaleString() || 0} icon="🔄" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Variable Selector */}
          <div className="lg:col-span-1 bg-white dark:bg-[#1a1a1a] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="w-5 h-5 text-blue-500" />
              <h2 className="text-xl font-bold">Variables</h2>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Sélectionnez une variable pour visualiser sa distribution.</p>
            
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
              {Object.keys(variables).map((varName) => {
                const varInfo = variables[varName];
                const isSelected = selectedVar === varName;
                return (
                  <button
                    key={varName}
                    onClick={() => setSelectedVar(varName)}
                    className={`w-full text-left px-4 py-3 rounded-xl transition-all border ${
                      isSelected 
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' 
                        : 'bg-gray-50 dark:bg-[#222] border-transparent hover:border-gray-300 dark:hover:border-gray-700'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className={`font-medium truncate mr-2 ${isSelected ? 'text-blue-700 dark:text-blue-400' : ''}`}>{varName}</span>
                      <span className="text-xs px-2 py-1 bg-gray-200 dark:bg-[#333] text-gray-600 dark:text-gray-300 rounded-md shrink-0">
                        {varInfo.type}
                      </span>
                    </div>
                    {varInfo.pct_manquantes > 0 && (
                      <div className="text-xs text-orange-500 mt-1">
                        {varInfo.pct_manquantes}% manquantes
                      </div>
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Right Column: Chart Display */}
          <div className="lg:col-span-2 bg-white dark:bg-[#1a1a1a] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm flex flex-col min-h-[400px]">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
              {activeDist?.type === "timeseries" ? "Évolution temporelle de" : "Distribution de"} <span className="text-blue-500">{selectedVar}</span>
            </h2>
            
            <div className="flex-1 w-full h-full min-h-[400px]">
              {!activeDist || !activeDist.data || activeDist.data.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-400">
                  <div className="text-center">
                    <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>Aucune donnée à visualiser pour cette variable.</p>
                  </div>
                </div>
              ) : activeDist.type === "categorical" ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={activeDist.data}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={140}
                      paddingAngle={2}
                      dataKey="value"
                      label={({name, percent}) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    >
                      {activeDist.data.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ borderRadius: '12px', border: '1px solid #333', background: 'rgba(20,20,20,0.9)', color: '#fff' }}
                      itemStyle={{ color: '#fff' }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : activeDist.type === "numeric" ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={activeDist.data} margin={{ top: 20, right: 30, left: 0, bottom: 50 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{fill: '#888', fontSize: 12}} />
                    <YAxis tick={{fill: '#888'}} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '12px', border: '1px solid #333', background: 'rgba(20,20,20,0.9)', color: '#fff' }}
                      itemStyle={{ color: '#fff' }}
                      cursor={{fill: 'rgba(255,255,255,0.1)'}}
                    />
                    <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                      {activeDist.data.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : activeDist.type === "datetime" || activeDist.type === "timeseries" ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={activeDist.data} margin={{ top: 20, right: 30, left: 0, bottom: 50 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{fill: '#888', fontSize: 12}} />
                    <YAxis tick={{fill: '#888'}} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '12px', border: '1px solid #333', background: 'rgba(20,20,20,0.9)', color: '#fff' }}
                    />
                    <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} dot={{r: 4, fill: '#3b82f6'}} />
                  </LineChart>
                </ResponsiveContainer>
              ) : null}
            </div>
          </div>
        </div>

        {/* Data Preview Table */}
        <div className="bg-white dark:bg-[#1a1a1a] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm overflow-hidden">
          <h2 className="text-xl font-bold mb-4">Aperçu des données (5 premières lignes)</h2>
          <div className="overflow-x-auto custom-scrollbar pb-4">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-gray-50 dark:bg-[#222] text-gray-600 dark:text-gray-300">
                <tr>
                  {Object.keys(preview[0] || {}).map(key => (
                    <th key={key} className="px-6 py-4 font-semibold whitespace-nowrap">{key}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {preview.map((row: any, i: number) => (
                  <tr key={i} className="hover:bg-gray-50/50 dark:hover:bg-white/5 transition">
                    {Object.values(row).map((val: any, j: number) => (
                      <td key={j} className="px-6 py-4 whitespace-nowrap text-gray-700 dark:text-gray-400">
                        {val === null ? <span className="text-gray-400 italic">null</span> : String(val)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          height: 6px;
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: rgba(150, 150, 150, 0.3);
          border-radius: 10px;
        }
      `}} />
    </div>
  );
}

function StatCard({ title, value, icon }: { title: string, value: string | number, icon: string }) {
  return (
    <div className="bg-white dark:bg-[#1a1a1a] border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm flex items-start gap-4">
      <div className="text-3xl bg-gray-50 dark:bg-[#222] p-3 rounded-xl">{icon}</div>
      <div>
        <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">{title}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
      </div>
    </div>
  );
}
