pub mod audio;
pub mod config;
pub mod embedded;
pub mod lang;
pub mod llm;
pub mod obs;
pub mod pipeline;
pub mod server;
pub mod subtitle;
pub mod vad;

use std::path::PathBuf;
use std::sync::Arc;

use anyhow::{Context, Result};
use clap::Parser;
use parking_lot::RwLock;
use tracing::{info, warn};

use crate::config::Config;

#[derive(Parser, Debug)]
#[command(
    name = "obs-live-translate",
    version,
    about = "Real-time AI subtitle overlay for OBS Studio"
)]
struct Cli {
    /// Path to config.toml. Defaults to ./config.toml, then ~/.config/obs-live-translate/config.toml.
    #[arg(long, short = 'c', global = true)]
    config: Option<PathBuf>,

    /// Override the bind host (e.g. 0.0.0.0 to expose on LAN).
    #[arg(long, global = true)]
    host: Option<String>,

    /// Override the bind port.
    #[arg(long, short = 'p', global = true)]
    port: Option<u16>,

    /// Open the admin panel in the default browser on launch.
    #[arg(long)]
    open: bool,

    /// Run as a headless background service (no console logs, no tray).
    #[arg(long)]
    headless: bool,
}

pub struct AppState {
    pub config: Arc<RwLock<Config>>,
    pub subtitle: Arc<subtitle::SubtitleHub>,
    pub pipeline: Arc<pipeline::PipelineHandle>,
    pub status: Arc<RwLock<AppStatus>>,
}

#[derive(Default, Clone, Debug)]
pub struct AppStatus {
    pub audio_active: bool,
    pub llm_connected: bool,
    pub obs_connected: bool,
    pub last_error: Option<String>,
    pub last_subtitle_at: Option<chrono::DateTime<chrono::Utc>>,
}

fn resolve_config_path(cli_path: Option<PathBuf>) -> PathBuf {
    if let Some(p) = cli_path {
        return p;
    }
    let local = PathBuf::from("config.toml");
    if local.exists() {
        return local;
    }
    if let Some(mut dir) = dirs::config_dir() {
        dir.push("obs-live-translate");
        dir.push("config.toml");
        return dir;
    }
    local
}

#[tokio::main]
async fn main() -> Result<()> {
    init_tracing();
    let cli = Cli::parse();

    let cfg_path = resolve_config_path(cli.config.clone());
    info!(path = %cfg_path.display(), "loading config");
    let mut cfg = Config::load_or_create(&cfg_path)
        .with_context(|| format!("load config {}", cfg_path.display()))?;

    if let Some(host) = &cli.host {
        cfg.server.host = host.clone();
    }
    if let Some(port) = cli.port {
        cfg.server.port = port;
    }

    let subtitle = Arc::new(subtitle::SubtitleHub::default());
    let pipeline = Arc::new(pipeline::PipelineHandle::new());
    let status = Arc::new(RwLock::new(AppStatus::default()));

    let state = Arc::new(AppState {
        config: Arc::new(RwLock::new(cfg.clone())),
        subtitle: subtitle.clone(),
        pipeline: pipeline.clone(),
        status: status.clone(),
    });

    // Start the audio -> LLM pipeline.
    pipeline::spawn(state.clone(), cfg_path.clone());

    // Start the OBS WebSocket client (auto-connect, dock management).
    let _obs = obs::spawn(state.clone());

    // Start the HTTP / WebSocket server (admin + overlay + OBS dock proxy).
    let server_cfg = cfg.server.clone();
    let server_state = state.clone();
    let server_task = tokio::spawn(async move {
        if let Err(e) = server::serve(server_state, server_cfg).await {
            warn!(error = %e, "server exited");
        }
    });

    if cli.open {
        let url = format!("http://{}:{}/admin", cfg.server.host, cfg.server.port);
        if let Err(e) = open_in_browser(&url) {
            warn!(error = %e, "failed to open admin page");
        }
    }

    info!(
        host = %cfg.server.host,
        port = cfg.server.port,
        "obs-live-translate running"
    );

    // Wait for Ctrl-C / SIGTERM.
    tokio::select! {
        _ = tokio::signal::ctrl_c() => {
            info!("ctrl-c received, shutting down");
        }
        _ = server_task => {
            warn!("server task ended unexpectedly");
        }
    }

    pipeline.shutdown().await;
    Ok(())
}

fn init_tracing() {
    use tracing_subscriber::{fmt, EnvFilter};
    let filter =
        EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info,obs_live_translate=info"));
    fmt().with_env_filter(filter).with_target(false).init();
}

fn open_in_browser(url: &str) -> Result<()> {
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("rundll32.exe")
            .args(["url.dll,FileProtocolHandler", url])
            .spawn()?;
    }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open").arg(url).spawn()?;
    }
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open").arg(url).spawn()?;
    }
    Ok(())
}
