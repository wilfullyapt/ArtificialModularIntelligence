use clap::{Parser, Subcommand, ValueEnum};
use std::collections::HashMap;
use std::path::Path;
use colored::*;
use std::env;
use std::fs;

#[derive(Parser)]
#[clap(about = "CLI tool for Artificial Modular Intelligence")]
struct Args {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Analyze code statistics in a directory
    Add,
    /// Install repostats to ~/.local/bin
    Install,
    /// Uninstall repostats from ~/.local/bin
    Uninstall,
}

fn main() {
    let args = Args::parse();
    match args.command {
        Command::Run => run(),
        Command::Install => install(),
        Command::Uninstall => uninstall(),
    }
}

fn install() {
    let home_dir = env::var("HOME").expect("HOME environment variable not set");
    let local_bin = Path::new(&home_dir).join(".local").join("bin");
    let local_bin_str = local_bin.to_str().expect("Invalid path");

    // Check if ~/.local/bin is in $PATH
    let path_env = env::var("PATH").unwrap_or_default();
    let path_dirs: Vec<&str> = path_env.split(':').collect();
    if !path_dirs.contains(&local_bin_str) {
        println!(
            "Warning: {} is not in your $PATH. Add it to use repostats globally.",
            local_bin.display()
        );
    }

    // Create ~/.local/bin if it doesn’t exist
    if !local_bin.exists() {
        if let Err(e) = fs::create_dir_all(&local_bin) {
            eprintln!("Failed to create {}: {}", local_bin.display(), e);
            std::process::exit(1);
        }
    }

    // Copy the current executable to ~/.local/bin/repostats
    let current_exe = env::current_exe().expect("Failed to get current executable path");
    let dest = local_bin.join("repostats");
    if let Err(e) = fs::copy(&current_exe, &dest) {
        eprintln!("Failed to install repostats: {}", e);
        std::process::exit(1);
    }

    println!("repostats installed successfully to {}", dest.display());
}

fn uninstall() {
    let home_dir = env::var("HOME").expect("HOME environment variable not set");
    let local_bin = Path::new(&home_dir).join(".local").join("bin");
    let dest = local_bin.join("repostats");

    if dest.exists() {
        if let Err(e) = fs::remove_file(&dest) {
            eprintln!("Failed to uninstall repostats: {}", e);
            std::process::exit(1);
        }
        println!("repostats uninstalled successfully");
    } else {
        println!("repostats is not installed in {}", local_bin.display());
    }
}
