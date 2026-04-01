from src.integration.Ollama_Integration_Hub import (
    FALLBACK_MODEL,
    IntelligentModelSelector,
    OllamaModel,
)


def make_model(name, capabilities, perf):
    return OllamaModel(
        name=name,
        size=1000,
        digest="abc",
        modified_at="now",
        family="m",
        capabilities=capabilities,
        performance_rating=perf,
    )


def test_select_optimal_model_code_analysis():
    selector = IntelligentModelSelector()
    model_code = make_model("code_model", ["code_analysis", "debugging"], 0.95)
    model_conv = make_model("conv_model", ["conversation"], 0.8)

    available = {model_code.name: model_code, model_conv.name: model_conv}
    selected = selector.select_optimal_model(available, "code_analysis")
    assert selected == model_code.name


def test_select_optimal_model_fallback():
    selector = IntelligentModelSelector()
    selected = selector.select_optimal_model({}, "random_intent")
    assert selected == FALLBACK_MODEL


def test_analyze_message_intent():
    selector = IntelligentModelSelector()
    assert selector.analyze_message_intent("Please help me debug this function") == "code_analysis"
    assert (
        selector.analyze_message_intent("Write a tutorial about how to use the API")
        == "documentation"
    )
