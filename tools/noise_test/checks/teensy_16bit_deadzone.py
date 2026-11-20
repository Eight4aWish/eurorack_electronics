import numpy as np
rng = np.random.default_rng(1)
lsb16 = 1/32768                      # one 16-bit step, full scale = 1
fs_sine_rms = 1/np.sqrt(2)
# the PCM3060 ADC's hiss: 99 dB dynamic range (A-wt, datasheet) below a full-scale sine; take flat ~1.5 dB more
for dr in (99.0, 97.5):
    sigma = fs_sine_rms * 10**(-dr/20)
    x = rng.normal(0, sigma, 2_000_000)                     # the 24-bit word, near enough continuous
    code_in = np.floor(x / lsb16)                           # Teensy: top 16 bits of the I2S word (truncation)
    out = np.trunc((code_in / 32768) * 32767)               # noise_stream.h: /32768, *32767, (int16_t) cast
    print(f"hiss {sigma/lsb16:.2f} steps rms; 16-bit input word rms {np.std(code_in):.2f} steps; "
          f"out rms {np.std(out):.4f} steps -> passes {20*np.log10(np.std(out)/(sigma/lsb16)+1e-12):.1f} dB of the hiss; "
          f"share of samples out non-zero {np.mean(out!=0)*100:.2f}%")
