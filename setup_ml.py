import subprocess, sys, os, logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def print_header(text):
    logger.info("\n" + "="*60)
    logger.info(f"  {text}")
    logger.info("="*60)

def install_requirements():
    print_header("Installing Dependencies")
    
    try:
        logger.info("Installing ML/AI packages...")
        logger.info("Including TensorFlow with GPU support for RTX 2050...\n")
        
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"]
        )
        
        logger.info("\nDependencies installed successfully!")
        return True
    except Exception as e:
        logger.error(f"Installation failed: {e}")
        logger.info("\nTroubleshooting:")
        logger.info("   - Ensure you have Python 3.8+ installed")
        logger.info("   - Try: pip install --upgrade pip setuptools wheel")
        return False

def verify_installation():
    print_header("Verifying Installation")
    
    packages = ["tensorflow", "sklearn", "numpy", "pandas"]
    all_good = True
    
    for package in packages:
        try:
            __import__(package)
            logger.info(f"{package:15} - OK")
        except ImportError:
            logger.info(f"{package:15} - MISSING")
            all_good = False
    
    return all_good

def check_gpu():
    print_header("Checking GPU Support")
    
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices("GPU")
        
        if gpus:
            logger.info(f"GPU Found: {len(gpus)} device(s)")
            for i, gpu in enumerate(gpus):
                logger.info(f"   Device {i}: {gpu}")
            
            logger.info("\nGPU Setup Tips for RTX 2050:")
            logger.info("   1. Ensure NVIDIA driver is installed")
            logger.info("   2. Install CUDA Toolkit 11.8+")
            logger.info("   3. Install cuDNN 8.6+")
            logger.info("   4. Verify: nvidia-smi in terminal")
            
            return True
        else:
            logger.info("No GPU found. Model will run on CPU.")
            logger.info("\nTo enable GPU:")
            logger.info("   1. Install NVIDIA GPU driver")
            logger.info("   2. pip install tensorflow[and-cuda]")
            logger.info("   3. Reboot and run this script again")
            return False
    except Exception as e:
        logger.error(f"GPU check failed: {e}")
        return False

def setup_directories():
    print_header("Setting Up Directories")
    
    directories = ["data", "ml_models/trained_models", "logs"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"{directory:30} - Ready")
    
    return True

def show_next_steps():
    print_header("Next Steps")
    
    logger.info("\n1. COLLECT DATA:")
    logger.info("   Make sure your database has weather data (90+ days recommended)")
    logger.info("   Run: python train.py")
    logger.info("")
    logger.info("2. TRAINING WILL:")
    logger.info("   - Collect historical weather data")
    logger.info("   - Preprocess and normalize features")
    logger.info("   - Train neural network on your RTX 2050")
    logger.info("   - Save trained model to ml_models/trained_models/")
    logger.info("")
    logger.info("3. AFTER TRAINING:")
    logger.info("   - Update config.py: Set use_model: True")
    logger.info("   - Restart Flask app")
    logger.info("   - Model will now make predictions!")
    logger.info("")
    logger.info("4. EXPECTED TRAINING TIME:")
    logger.info("   - With GPU (RTX 2050): 5-15 minutes")
    logger.info("   - Without GPU (CPU): 30-60 minutes")
    logger.info("   - Depends on data size")

def main():
    logger.info("\n")
    logger.info("╔" + "="*58 + "╗")
    logger.info("║" + "ML MODEL SETUP - COASTAL THREAT ALERT".center(58) + "║")
    logger.info("╚" + "="*58 + "╝")
    
    if not install_requirements():
        logger.error("Setup failed at dependency installation")
        return False
    
    if not setup_directories():
        logger.error("Setup failed at directory setup")
        return False
    
    if not verify_installation():
        logger.warning("Some packages are missing. Please install manually:")
        logger.warning("   pip install -r requirements.txt")
        return False
    
    check_gpu()
    show_next_steps()
    
    logger.info("\n" + "="*60)
    logger.info("SETUP COMPLETE! You're ready to train the model!")
    logger.info("="*60)
    
    logger.info("\nRun this to start training:")
    logger.info("   python train.py\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nSetup interrupted by user")
        sys.exit(1)
