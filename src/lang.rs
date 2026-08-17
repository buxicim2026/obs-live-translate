//! Lightweight language detection used to decide whether the model's
//! transcript should be passed through (already Chinese) or whether we
//! should ask the model to translate it. We use a character-class heuristic
//! that works well in practice for the live subtitle use-case: the LLM
//! already does the heavy lifting; this is only a routing decision.

use unicode_script::Script;

#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
pub enum Language {
    Chinese,
    English,
    Japanese,
    Korean,
    Other,
}

pub fn detect(text: &str) -> Language {
    if text.is_empty() {
        return Language::Other;
    }

    let mut han = 0u32;
    let mut latin = 0u32;
    let mut hiragana = 0u32;
    let mut katakana = 0u32;
    let mut hangul = 0u32;
    let mut other = 0u32;
    let mut total = 0u32;

    for ch in text.chars() {
        if ch.is_whitespace() || ch.is_ascii_punctuation() {
            continue;
        }
        total += 1;
        match Script::from(ch) {
            Script::Han => han += 1,
            Script::Latin => latin += 1,
            Script::Hiragana => hiragana += 1,
            Script::Katakana => katakana += 1,
            Script::Hangul => hangul += 1,
            _ => other += 1,
        }
    }

    if total == 0 {
        return Language::Other;
    }

    if han as f32 / total as f32 > 0.3 {
        return Language::Chinese;
    }
    if (hiragana + katakana) as f32 / total as f32 > 0.3 {
        return Language::Japanese;
    }
    if hangul as f32 / total as f32 > 0.3 {
        return Language::Korean;
    }
    if latin as f32 / total as f32 > 0.5 {
        return Language::English;
    }
    Language::Other
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detects_chinese() {
        assert_eq!(detect("你好，世界"), Language::Chinese);
        assert_eq!(detect("我在测试 OBS 字幕插件"), Language::Chinese);
    }

    #[test]
    fn detects_english() {
        assert_eq!(detect("Hello, this is a test."), Language::English);
    }

    #[test]
    fn detects_japanese() {
        assert_eq!(detect("こんにちは、テスト中"), Language::Japanese);
    }
}
