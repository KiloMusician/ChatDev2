import React, { useState } from 'react';
import { motion } from 'framer-motion';

export interface ConfigSection {
  id: string;
  title: string;
  description: string;
  options: ConfigOption[];
}

export interface ConfigOption {
  id: string;
  label: string;
  type: 'boolean' | 'string' | 'number' | 'select' | 'range';
  value: any;
  defaultValue: any;
  options?: { value: any; label: string }[];
  min?: number;
  max?: number;
  step?: number;
  description?: string;
}

interface AdvancedConfigPanelProps {
  sections: ConfigSection[];
  onChange: (sectionId: string, optionId: string, value: any) => void;
  onReset: (sectionId: string) => void;
  onExport: () => void;
  onImport: (config: any) => void;
}

export function AdvancedConfigPanel({ 
  sections, 
  onChange, 
  onReset, 
  onExport, 
  onImport 
}: AdvancedConfigPanelProps) {
  const [activeSection, setActiveSection] = useState(sections[0]?.id);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredSections = sections.filter(section =>
    section.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    section.options.some(option => 
      option.label.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  const renderConfigOption = (option: ConfigOption, sectionId: string) => {
    const handleChange = (newValue: any) => {
      onChange(sectionId, option.id, newValue);
    };

    switch (option.type) {
      case 'boolean':
        return (
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <label className="text-sm font-medium text-cyan-300">{option.label}</label>
              {option.description && (
                <p className="text-xs text-gray-400 mt-1">{option.description}</p>
              )}
            </div>
            <button
              onClick={() => handleChange(!option.value)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                option.value ? 'bg-cyan-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  option.value ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        );

      case 'string':
        return (
          <div>
            <label className="text-sm font-medium text-cyan-300">{option.label}</label>
            {option.description && (
              <p className="text-xs text-gray-400 mt-1 mb-2">{option.description}</p>
            )}
            <input
              type="text"
              value={option.value}
              onChange={(e) => handleChange(e.target.value)}
              className="w-full px-3 py-2 bg-black/50 border border-gray-600 rounded text-cyan-100 focus:border-cyan-400 focus:outline-none"
            />
          </div>
        );

      case 'number':
        return (
          <div>
            <label className="text-sm font-medium text-cyan-300">{option.label}</label>
            {option.description && (
              <p className="text-xs text-gray-400 mt-1 mb-2">{option.description}</p>
            )}
            <input
              type="number"
              value={option.value}
              onChange={(e) => handleChange(Number(e.target.value))}
              min={option.min}
              max={option.max}
              step={option.step}
              className="w-full px-3 py-2 bg-black/50 border border-gray-600 rounded text-cyan-100 focus:border-cyan-400 focus:outline-none"
            />
          </div>
        );

      case 'range':
        return (
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-cyan-300">{option.label}</label>
              <span className="text-sm text-cyan-400">{option.value}</span>
            </div>
            {option.description && (
              <p className="text-xs text-gray-400 mb-2">{option.description}</p>
            )}
            <input
              type="range"
              value={option.value}
              onChange={(e) => handleChange(Number(e.target.value))}
              min={option.min || 0}
              max={option.max || 100}
              step={option.step || 1}
              className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        );

      case 'select':
        return (
          <div>
            <label className="text-sm font-medium text-cyan-300">{option.label}</label>
            {option.description && (
              <p className="text-xs text-gray-400 mt-1 mb-2">{option.description}</p>
            )}
            <select
              value={option.value}
              onChange={(e) => handleChange(e.target.value)}
              className="w-full px-3 py-2 bg-black/50 border border-gray-600 rounded text-cyan-100 focus:border-cyan-400 focus:outline-none"
            >
              {option.options?.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-gray-800">
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="bg-black/40 border border-cyan-400/30 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-600 bg-black/60">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-cyan-300">⚙️ Advanced Configuration</h2>
          <div className="flex gap-2">
            <button
              onClick={onExport}
              className="px-3 py-1 bg-blue-600/30 border border-blue-400 text-blue-300 rounded text-sm hover:bg-blue-600/50 transition-all"
            >
              Export
            </button>
            <label className="px-3 py-1 bg-green-600/30 border border-green-400 text-green-300 rounded text-sm hover:bg-green-600/50 transition-all cursor-pointer">
              Import
              <input
                type="file"
                accept=".json"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                      try {
                        const result = event.target?.result;
                        if (typeof result === 'string') {
                          const config = JSON.parse(result);
                          onImport(config);
                        }
                      } catch (error) {
                        console.error('Failed to import config:', error);
                      }
                    };
                    reader.readAsText(file);
                  }
                }}
              />
            </label>
          </div>
        </div>

        {/* Search */}
        <input
          type="text"
          placeholder="Search configuration options..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 bg-black/50 border border-gray-600 rounded text-cyan-100 focus:border-cyan-400 focus:outline-none"
        />
      </div>

      <div className="flex h-96">
        {/* Section Navigation */}
        <div className="w-64 border-r border-gray-600 bg-black/20">
          <div className="p-2 space-y-1">
            {filteredSections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full text-left px-3 py-2 rounded text-sm transition-all ${
                  activeSection === section.id
                    ? 'bg-cyan-600/30 border border-cyan-400 text-cyan-300'
                    : 'text-gray-300 hover:bg-white/10'
                }`}
              >
                {section.title}
              </button>
            ))}
          </div>
        </div>

        {/* Configuration Options */}
        <div className="flex-1 p-4 overflow-y-auto">
          {(() => {
            const activeConfigSection = filteredSections.find(s => s.id === activeSection);
            if (!activeConfigSection) return null;

            return (
              <motion.div
                key={activeSection}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-cyan-300">
                      {activeConfigSection.title}
                    </h3>
                    <p className="text-sm text-gray-400 mt-1">
                      {activeConfigSection.description}
                    </p>
                  </div>
                  <button
                    onClick={() => onReset(activeSection || '')}
                    className="px-3 py-1 bg-red-600/30 border border-red-400 text-red-300 rounded text-sm hover:bg-red-600/50 transition-all"
                  >
                    Reset Section
                  </button>
                </div>

                <div className="space-y-6">
                  {activeConfigSection.options
                    .filter(option => 
                      searchTerm === '' || 
                      option.label.toLowerCase().includes(searchTerm.toLowerCase())
                    )
                    .map((option) => (
                      <div key={option.id} className="p-4 bg-black/40 border border-gray-600 rounded">
                        {renderConfigOption(option, activeSection || '')}
                      </div>
                    ))}
                </div>
              </motion.div>
            );
          })()}
        </div>
      </div>
    </div>
  );
}