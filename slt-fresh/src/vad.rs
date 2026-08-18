//! Energy-based Voice Activity Detection and a tiny spectral-flatness music
//! detector. Lightweight enough to run on every PCM chunk the audio thread
//! produces, before we hand it to the LLM.

use crate::config::FilterConfig;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SegmentKind {
    Silence,
    Music,
    Speech,
}

#[derive(Debug, Clone)]
pub struct Decision {
    pub kind: SegmentKind,
    pub rms: f32,
    pub flatness: f32,
    pub voiced_ms: u32,
}

pub struct Vad {
    cfg: FilterConfig,
    voiced_ms: u32,
    /// Number of consecutive non-silent frames (for end-of-segment debounce).
    silence_ms: u32,
}

impl Vad {
    pub fn new(cfg: FilterConfig) -> Self {
        Self {
            cfg,
            voiced_ms: 0,
            silence_ms: 0,
        }
    }

    /// Decide what kind of audio a frame is. `pcm` is mono s16le samples at
    /// the audio thread's native rate.
    pub fn decide(&mut self, pcm: &[i16], sample_rate: u32) -> Decision {
        let rms = rms(pcm);
        let flatness = spectral_flatness(pcm, sample_rate);

        if rms < self.cfg.silence_rms {
            self.silence_ms = self.silence_ms.saturating_add(frame_ms(pcm, sample_rate));
            return Decision {
                kind: SegmentKind::Silence,
                rms,
                flatness,
                voiced_ms: 0,
            };
        }

        if flatness > self.cfg.music_spectral_flatness {
            // Music often has high RMS but tonal balance; treat it as music
            // so we skip sending it to the LLM.
            self.voiced_ms = 0;
            self.silence_ms = 0;
            return Decision {
                kind: SegmentKind::Music,
                rms,
                flatness,
                voiced_ms: 0,
            };
        }

        self.silence_ms = 0;
        self.voiced_ms = self
            .voiced_ms
            .saturating_add(frame_ms(pcm, sample_rate));
        Decision {
            kind: SegmentKind::Speech,
            rms,
            flatness,
            voiced_ms: self.voiced_ms,
        }
    }

    pub fn reset(&mut self) {
        self.voiced_ms = 0;
        self.silence_ms = 0;
    }

    pub fn config(&self) -> &FilterConfig {
        &self.cfg
    }
}

fn frame_ms(pcm: &[i16], rate: u32) -> u32 {
    if rate == 0 {
        return 0;
    }
    ((pcm.len() as u64 * 1000) / rate as u64) as u32
}

pub fn rms(pcm: &[i16]) -> f32 {
    if pcm.is_empty() {
        return 0.0;
    }
    let mut sum = 0.0f64;
    for &s in pcm {
        let f = s as f64 / i16::MAX as f64;
        sum += f * f;
    }
    ((sum / pcm.len() as f64) as f32).sqrt()
}

/// Naive spectral flatness via zero-crossing proxy + energy variance.
/// Cheap, no FFT, good enough to distinguish sustained tonal music from
/// transient-heavy speech.
pub fn spectral_flatness(pcm: &[i16], _rate: u32) -> f32 {
    if pcm.len() < 8 {
        return 0.0;
    }
    let mut crossings = 0usize;
    for w in pcm.windows(2) {
        if (w[0] >= 0) != (w[1] >= 0) {
            crossings += 1;
        }
    }
    let zcr = crossings as f32 / pcm.len() as f32;

    // Variance of the absolute amplitude.
    let mut acc = 0.0f64;
    for &s in pcm {
        acc += s.abs() as f64;
    }
    let mean = acc / pcm.len() as f64;
    let mut var = 0.0f64;
    for &s in pcm {
        let d = s.abs() as f64 - mean;
        var += d * d;
    }
    var /= pcm.len() as f64;
    let cv = if mean > 0.0 { var.sqrt() / mean } else { 0.0 } as f32;

    // Music tends to have moderate ZCR with very low coefficient of
    // variation (constant amplitude). Combine both into a single score.
    let score = (1.0 - cv).clamp(0.0, 1.0) * (1.0 - (zcr - 0.15).abs() * 2.5).clamp(0.0, 1.0);
    score
}
