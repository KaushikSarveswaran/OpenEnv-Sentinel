## ADDED Requirements

### Requirement: Provider selection
The system SHALL display provider options (Azure OpenAI, OpenRouter) as clickable tabs or cards in the Run view. Selecting a provider SHALL reveal its configuration form.

#### Scenario: User selects Azure OpenAI
- **WHEN** the user clicks "Azure OpenAI"
- **THEN** the Azure OpenAI configuration form is shown with fields for endpoint, deployment, API key, and API version
- **AND** the deployment field SHALL be pre-populated with the default value from `AZURE_OPENAI_DEPLOYMENT` env var if set

#### Scenario: User selects OpenRouter
- **WHEN** the user clicks "OpenRouter"
- **THEN** the OpenRouter configuration form is shown with fields for API key, site URL, and site name
- **AND** a model dropdown SHALL appear pre-populated with curated free models

### Requirement: OpenRouter free model dropdown
The system SHALL display a dropdown selector for OpenRouter models pre-populated with the following free models from OpenRouter:

| Model ID | Display Name | Context |
|---|---|---|
| `google/gemma-4-31b-it:free` | Google: Gemma 4 31B | 262K |
| `google/gemma-4-26b-a4b-it:free` | Google: Gemma 4 26B A4B | 262K |
| `qwen/qwen3-coder:free` | Qwen: Qwen3 Coder 480B A35B | 262K |
| `qwen/qwen3-next-80b-a3b-instruct:free` | Qwen: Qwen3 Next 80B A3B | 262K |
| `nvidia/nemotron-3-super-120b-a12b:free` | NVIDIA: Nemotron 3 Super | 262K |
| `inclusionai/ling-2.6-1t:free` | inclusionAI: Ling-2.6-1T | 262K |
| `inclusionai/ling-2.6-flash:free` | inclusionAI: Ling-2.6-flash | 262K |
| `meta-llama/llama-3.3-70b-instruct:free` | Meta: Llama 3.3 70B Instruct | 65K |
| `openai/gpt-oss-120b:free` | OpenAI: gpt-oss-120b | 131K |
| `openai/gpt-oss-20b:free` | OpenAI: gpt-oss-20b | 131K |
| `nousresearch/hermes-3-llama-3.1-405b:free` | Nous: Hermes 3 405B Instruct | 131K |
| `minimax/minimax-m2.5:free` | MiniMax: MiniMax M2.5 | 196K |

The default selected model SHALL be `google/gemma-4-31b-it:free`. The user SHALL also be able to type a custom model ID not in the list.

#### Scenario: User sees free model dropdown
- **WHEN** the user selects OpenRouter as the provider
- **THEN** a dropdown appears listing the curated free models with display names
- **AND** `google/gemma-4-31b-it:free` is selected by default

#### Scenario: User selects a free model from dropdown
- **WHEN** the user clicks the model dropdown and selects `meta-llama/llama-3.3-70b-instruct:free`
- **THEN** that model ID is set as the current model selection

#### Scenario: User types a custom model ID
- **WHEN** the user types a model ID not in the dropdown list (e.g., `anthropic/claude-sonnet-4`)
- **THEN** the typed model ID is accepted as the current selection

### Requirement: Default model population
The system SHALL pre-populate the default model/deployment when a provider is selected, using environment variables if available or built-in defaults otherwise.

#### Scenario: Azure defaults from environment
- **WHEN** the user selects Azure OpenAI and `AZURE_OPENAI_DEPLOYMENT` is set in the environment
- **THEN** the deployment field is pre-filled with that value

#### Scenario: Azure defaults without environment
- **WHEN** the user selects Azure OpenAI and no Azure env vars are set
- **THEN** the deployment field shows a placeholder prompting the user to enter a deployment name

#### Scenario: OpenRouter defaults from environment
- **WHEN** the user selects OpenRouter and `MODEL_NAME` env var is set and it matches a model in the dropdown
- **THEN** that model is pre-selected in the dropdown instead of the built-in default

### Requirement: Add multiple models
The system SHALL allow users to add multiple models within a selected provider. Each added model SHALL appear in a list and be included when a run is triggered.

#### Scenario: User adds a model to Azure OpenAI
- **WHEN** the user has Azure OpenAI selected and enters a deployment name and clicks "Add Model"
- **THEN** the model is added to the model list for Azure OpenAI
- **AND** the user can continue adding more models

#### Scenario: User adds a free model from dropdown to OpenRouter
- **WHEN** the user has OpenRouter selected and picks a model from the dropdown and clicks "Add Model"
- **THEN** the selected model is added to the model list for OpenRouter

#### Scenario: User adds a custom model to OpenRouter
- **WHEN** the user has OpenRouter selected and types a custom model ID and clicks "Add Model"
- **THEN** the custom model is added to the model list for OpenRouter

#### Scenario: User removes a model
- **WHEN** the user clicks the remove button on a model in the list
- **THEN** that model is removed from the run queue

### Requirement: Mixed provider runs
The system SHALL allow models from both Azure OpenAI and OpenRouter to be queued in the same session. Runs SHALL execute sequentially, one model at a time.

#### Scenario: Models from two providers queued
- **WHEN** the user adds an Azure deployment and an OpenRouter model and clicks "Run"
- **THEN** inference runs sequentially — first the Azure model, then the OpenRouter model (or vice versa based on queue order)
