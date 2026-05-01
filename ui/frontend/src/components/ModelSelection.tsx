import { useState } from "react";
import type { AzureDefaults, OpenRouterDefaults, ModelQueueItem, FreeModel } from "../types";

interface Props {
  azure: AzureDefaults;
  openrouter: OpenRouterDefaults;
  queue: ModelQueueItem[];
  onAdd: (item: ModelQueueItem) => void;
  onRemove: (index: number) => void;
}

export default function ModelSelection({ azure, openrouter, queue, onAdd, onRemove }: Props) {
  const [activeTab, setActiveTab] = useState<"azure" | "openrouter">("openrouter");

  // Azure form state
  const [azEndpoint, setAzEndpoint] = useState(azure.endpoint);
  const [azDeployment, setAzDeployment] = useState(azure.deployment);
  const [azKey, setAzKey] = useState(azure.api_key);
  const [azVersion, setAzVersion] = useState(azure.api_version);

  // OpenRouter form state
  const [orKey, setOrKey] = useState(openrouter.api_key);
  const [orModel, setOrModel] = useState(openrouter.model_id);
  const [orCustom, setOrCustom] = useState("");
  const [orSiteUrl, setOrSiteUrl] = useState(openrouter.site_url);
  const [orSiteName, setOrSiteName] = useState(openrouter.site_name);
  const [useCustomModel, setUseCustomModel] = useState(false);

  const handleAddAzure = () => {
    if (!azDeployment) return;
    onAdd({
      provider: "azure",
      model_name: azDeployment,
      config: { endpoint: azEndpoint, api_key: azKey, api_version: azVersion },
    });
  };

  const handleAddOpenRouter = () => {
    const modelId = useCustomModel ? orCustom : orModel;
    if (!modelId) return;
    onAdd({
      provider: "openrouter",
      model_name: modelId,
      config: { api_key: orKey, site_url: orSiteUrl, site_name: orSiteName },
    });
  };

  return (
    <div className="model-selection">
      <div className="provider-tabs">
        <button
          className={`tab ${activeTab === "azure" ? "active" : ""}`}
          onClick={() => setActiveTab("azure")}
        >
          Azure OpenAI
        </button>
        <button
          className={`tab ${activeTab === "openrouter" ? "active" : ""}`}
          onClick={() => setActiveTab("openrouter")}
        >
          OpenRouter
        </button>
      </div>

      {activeTab === "azure" && (
        <div className="provider-form">
          <div className="form-group">
            <label>Endpoint</label>
            <input value={azEndpoint} onChange={(e) => setAzEndpoint(e.target.value)} placeholder="https://your-resource.openai.azure.com" />
          </div>
          <div className="form-group">
            <label>Deployment</label>
            <input value={azDeployment} onChange={(e) => setAzDeployment(e.target.value)} placeholder="Enter deployment name" />
          </div>
          <div className="form-group">
            <label>API Key</label>
            <input type="password" value={azKey} onChange={(e) => setAzKey(e.target.value)} placeholder="Azure API key" />
          </div>
          <div className="form-group">
            <label>API Version</label>
            <input value={azVersion} onChange={(e) => setAzVersion(e.target.value)} />
          </div>
          <button className="btn btn-add" onClick={handleAddAzure}>Add Model</button>
        </div>
      )}

      {activeTab === "openrouter" && (
        <div className="provider-form">
          <div className="form-group">
            <label>API Key</label>
            <input type="password" value={orKey} onChange={(e) => setOrKey(e.target.value)} placeholder="sk-or-..." />
          </div>
          <div className="form-group">
            <label>Model</label>
            <div className="model-select-row">
              {!useCustomModel ? (
                <select value={orModel} onChange={(e) => setOrModel(e.target.value)}>
                  {openrouter.free_models.map((m: FreeModel) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.context})
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  value={orCustom}
                  onChange={(e) => setOrCustom(e.target.value)}
                  placeholder="e.g., anthropic/claude-sonnet-4"
                />
              )}
              <button className="btn btn-sm" onClick={() => setUseCustomModel(!useCustomModel)}>
                {useCustomModel ? "Use Dropdown" : "Custom"}
              </button>
            </div>
          </div>
          <div className="form-group">
            <label>Site URL (optional)</label>
            <input value={orSiteUrl} onChange={(e) => setOrSiteUrl(e.target.value)} placeholder="https://yoursite.com" />
          </div>
          <div className="form-group">
            <label>Site Name (optional)</label>
            <input value={orSiteName} onChange={(e) => setOrSiteName(e.target.value)} placeholder="My App" />
          </div>
          <button className="btn btn-add" onClick={handleAddOpenRouter}>Add Model</button>
        </div>
      )}

      {queue.length > 0 && (
        <div className="model-queue">
          <h3>Model Queue ({queue.length})</h3>
          {queue.map((item, i) => (
            <div key={i} className="queue-item">
              <span className="provider-badge">{item.provider === "azure" ? "Azure" : "OR"}</span>
              <span className="model-name">{item.model_name}</span>
              <button className="btn btn-remove" onClick={() => onRemove(i)}>×</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
