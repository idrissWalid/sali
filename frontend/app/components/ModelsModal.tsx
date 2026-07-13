"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface ModelInfo {
  id: string;
  name: string;
  type: string;
  features: string[];
  metrics: Record<string, any>;
  created_at: string;
}

interface ModelsModalProps {
  sessionId: string;
  onClose: () => void;
  isOpen?: boolean;
}

export default function ModelsModal({ sessionId, onClose, isOpen = true }: ModelsModalProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (isOpen) {
      fetchModels();
    }
  }, [sessionId, isOpen]);

  if (!isOpen) return null;

  const fetchModels = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/api/models/${sessionId}`);
      if (!res.ok) throw new Error("Erreur de récupération des modèles");
      const data = await res.json();
      setModels(data.models || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (modelId: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    window.open(`${apiUrl}/api/models/${modelId}/download`, '_blank');
  };

  const handleDashboard = (modelId: string) => {
    router.push(`/dashboard/model/${modelId}`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#1e1e24] border border-[#2d2d3a] rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col">
        <div className="flex justify-between items-center p-4 border-b border-[#2d2d3a]">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            🚀 Modèles Entraînés
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            ✕
          </button>
        </div>

        <div className="p-4 overflow-y-auto max-h-[60vh] custom-scrollbar">
          {loading ? (
            <div className="text-center text-gray-400 py-8">Chargement des modèles...</div>
          ) : error ? (
            <div className="text-center text-red-400 py-8">{error}</div>
          ) : models.length === 0 ? (
            <div className="text-center text-gray-400 py-8">Aucun modèle entraîné dans cette session.</div>
          ) : (
            <div className="space-y-4">
              {models.map(model => (
                <div key={model.id} className="bg-[#26262e] rounded-lg p-4 border border-[#333342]">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="text-lg font-medium text-white">{model.name}</h3>
                      <span className="text-xs font-semibold px-2 py-1 rounded bg-[#333342] text-gray-300">
                        {model.type}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(model.created_at).toLocaleString()}
                    </div>
                  </div>

                  {model.metrics && Object.keys(model.metrics).length > 0 && (
                    <div className="mb-3">
                      <div className="text-sm text-gray-400 mb-1">Métriques :</div>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(model.metrics).map(([key, value]) => (
                          <div key={key} className="bg-[#1e1e24] p-2 rounded text-xs flex justify-between">
                            <span className="text-gray-400">{key}:</span>
                            <span className="text-white font-mono">{typeof value === 'number' ? value.toFixed(4) : String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {model.features && model.features.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm text-gray-400 mb-1">Variables d'entrée ({model.features.length}) :</div>
                      <div className="flex flex-wrap gap-1">
                        {model.features.map(feat => (
                          <span key={feat} className="text-xs bg-[#2d2d3a] text-gray-300 px-2 py-1 rounded">
                            {feat}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2 mt-4">
                    <button
                      onClick={() => handleDashboard(model.id)}
                      className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium py-2 px-4 rounded-md transition-all flex items-center justify-center gap-2"
                    >
                      <span>📊</span> Créer Dashboard
                    </button>
                    <button
                      onClick={() => handleDownload(model.id)}
                      className="flex-1 bg-[#333342] hover:bg-[#3d3d4e] text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
                    >
                      <span>📥</span> Télécharger (.pkl)
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
