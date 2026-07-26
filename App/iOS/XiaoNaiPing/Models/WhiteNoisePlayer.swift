import AVFoundation
import Combine
import Foundation

enum WhiteNoiseSound: String, CaseIterable, Hashable, Identifiable {
    case rain
    case ocean
    case fan
    case pink
    case dryer
    case cabin
    case shush

    var id: String { rawValue }

    var title: String {
        switch self {
        case .rain: "柔雨"
        case .ocean: "海浪"
        case .fan: "风扇"
        case .pink: "粉噪"
        case .dryer: "风筒"
        case .cabin: "机舱"
        case .shush: "长嘘"
        }
    }

    var subtitle: String {
        switch self {
        case .rain: "细密安静"
        case .ocean: "缓慢起伏"
        case .fan: "稳定低频"
        case .pink: "温和均衡"
        case .dryer: "暖暖包裹"
        case .cabin: "低低轰鸣"
        case .shush: "贴近安抚"
        }
    }

    var systemImage: String {
        switch self {
        case .rain: "cloud.rain"
        case .ocean: "water.waves"
        case .fan: "fan"
        case .pink: "waveform"
        case .dryer: "wind"
        case .cabin: "airplane"
        case .shush: "mouth"
        }
    }
}

final class WhiteNoisePlayer: ObservableObject {
    /// 全 App 共享一个播放器：哄睡时离开页面、切 tab 都不能断声。
    static let shared = WhiteNoisePlayer()

    @Published private(set) var isPlaying = false
    @Published private(set) var isPreparing = false
    @Published var selectedSound: WhiteNoiseSound = .rain {
        didSet { restartLoopIfNeeded() }
    }
    @Published var volume: Double = 0.34 {
        didSet {
            audioPlayer?.volume = Float(volume)
        }
    }

    private var generatedAudioURLs: [WhiteNoiseSound: URL] = [:]
    private var audioPlayer: AVAudioPlayer?
    private var generationTask: Task<Void, Never>?

    deinit {
        generationTask?.cancel()
        stop()
    }

    func toggle() {
        (isPlaying || isPreparing) ? stop() : play()
    }

    func play() {
        let sound = selectedSound
        generationTask?.cancel()

        if let url = existingAudioURL(for: sound) {
            startLoop(from: url)
            return
        }

        isPreparing = true
        generationTask = Task.detached(priority: .userInitiated) { [sound] in
            let result: Result<URL, Error>
            do {
                result = .success(try Self.writeGeneratedAudio(for: sound))
            } catch {
                result = .failure(error)
            }

            guard !Task.isCancelled else { return }

            await MainActor.run { [weak self] in
                guard let self else { return }
                self.isPreparing = false

                guard self.selectedSound == sound else { return }

                switch result {
                case .success(let url):
                    self.generatedAudioURLs[sound] = url
                    self.startLoop(from: url)
                case .failure:
                    self.stop()
                }
            }
        }
    }

    func stop() {
        generationTask?.cancel()
        generationTask = nil
        audioPlayer?.stop()
        audioPlayer = nil
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        isPlaying = false
        isPreparing = false
    }

    private func configureAudioSession() throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playback, mode: .default, options: [.mixWithOthers])
        try session.setActive(true)
    }

    private func restartLoopIfNeeded() {
        guard isPlaying else { return }
        play()
    }

    private static func makeBuffer(for sound: WhiteNoiseSound) throws -> AVAudioPCMBuffer {
        guard let format = audioFormat() else {
            throw WhiteNoisePlayerError.audioFormatUnavailable
        }

        let duration = duration(for: sound)
        let frameCount = AVAudioFrameCount(format.sampleRate * duration)
        guard let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frameCount) else {
            throw WhiteNoisePlayerError.bufferUnavailable
        }
        buffer.frameLength = frameCount

        guard let data = buffer.floatChannelData?[0] else {
            return buffer
        }

        var generator = WhiteNoiseBufferGenerator(sampleRate: format.sampleRate, seed: seed(for: sound))
        for frame in 0..<Int(frameCount) {
            data[frame] = generator.sample(for: sound) * 0.62
        }

        applyFade(to: data, frameCount: Int(frameCount), fadeFrames: Int(format.sampleRate * 0.08))
        return buffer
    }

    private func existingAudioURL(for sound: WhiteNoiseSound) -> URL? {
        if let bundledURL = bundledAudioURL(for: sound) {
            return bundledURL
        }

        if let cachedURL = generatedAudioURLs[sound],
           FileManager.default.fileExists(atPath: cachedURL.path) {
            return cachedURL
        }

        let generatedURL = Self.generatedAudioURL(for: sound)
        if FileManager.default.fileExists(atPath: generatedURL.path) {
            generatedAudioURLs[sound] = generatedURL
            return generatedURL
        }

        return nil
    }

    private func bundledAudioURL(for sound: WhiteNoiseSound) -> URL? {
        guard let fileName = sound.bundledAudioFileName else {
            return nil
        }
        return Bundle.main.url(forResource: fileName, withExtension: "mp3")
    }

    private func startLoop(from url: URL) {
        do {
            try configureAudioSession()
            audioPlayer?.stop()
            audioPlayer = nil

            let player = try AVAudioPlayer(contentsOf: url)
            player.numberOfLoops = -1
            player.volume = Float(volume)
            player.prepareToPlay()
            player.play()
            audioPlayer = player
            isPlaying = true
            isPreparing = false
        } catch {
            stop()
        }
    }

    private static func generatedAudioURL(for sound: WhiteNoiseSound) -> URL {
        let directory = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first
            ?? FileManager.default.temporaryDirectory
        return directory.appendingPathComponent("xiaonaiping-\(sound.rawValue)-white-noise.caf")
    }

    private static func writeGeneratedAudio(for sound: WhiteNoiseSound) throws -> URL {
        let format = try requireAudioFormat()
        let url = generatedAudioURL(for: sound)

        if FileManager.default.fileExists(atPath: url.path) {
            return url
        }

        let buffer = try makeBuffer(for: sound)
        let file = try AVAudioFile(forWriting: url, settings: format.settings)
        try file.write(from: buffer)
        return url
    }

    private static func audioFormat() -> AVAudioFormat? {
        AVAudioFormat(standardFormatWithSampleRate: 22_050, channels: 1)
    }

    private static func requireAudioFormat() throws -> AVAudioFormat {
        guard let format = audioFormat() else {
            throw WhiteNoisePlayerError.audioFormatUnavailable
        }
        return format
    }

    private static func applyFade(to data: UnsafeMutablePointer<Float>, frameCount: Int, fadeFrames: Int) {
        let safeFadeFrames = min(fadeFrames, frameCount / 2)
        guard safeFadeFrames > 0 else { return }

        for index in 0..<safeFadeFrames {
            let scale = Float(index) / Float(safeFadeFrames)
            data[index] *= scale
            data[frameCount - index - 1] *= scale
        }
    }

    private static func seed(for sound: WhiteNoiseSound) -> UInt64 {
        switch sound {
        case .rain:
            0x1234ABCD
        case .ocean:
            0x2234ABCD
        case .fan:
            0x3234ABCD
        case .pink:
            0x4234ABCD
        case .dryer:
            0x5234ABCD
        case .cabin:
            0x6234ABCD
        case .shush:
            0x7234ABCD
        }
    }

    private static func duration(for sound: WhiteNoiseSound) -> Double {
        switch sound {
        case .shush:
            14
        case .cabin:
            8
        default:
            6
        }
    }

}

private enum WhiteNoisePlayerError: Error {
    case audioFormatUnavailable
    case bufferUnavailable
}

private extension WhiteNoiseSound {
    var bundledAudioFileName: String? {
        switch self {
        case .dryer:
            "white_noise_dryer"
        case .cabin:
            "white_noise_cabin"
        case .shush:
            "white_noise_shush"
        case .rain, .ocean, .fan, .pink:
            nil
        }
    }
}

private struct WhiteNoiseBufferGenerator {
    let sampleRate: Double
    var randomState: UInt64
    var brownValue: Float = 0
    var pinkRows = [Float](repeating: 0, count: 7)
    var pinkCounter: UInt32 = 0
    var wavePhase: Double = 0
    var fanPhase: Double = 0
    var dryerPhase: Double = 0
    var cabinPhase: Double = 0
    var shushPhase: Double = 0
    var shushMouthLow: Float = 0
    var shushMouthBand: Float = 0
    var shushAirLow: Float = 0
    var shushAirBand: Float = 0
    var shushWarmth: Float = 0
    var shushSmoothed: Float = 0
    var previousShushNoise: Float = 0

    init(sampleRate: Double, seed: UInt64) {
        self.sampleRate = sampleRate
        randomState = seed
    }

    mutating func sample(for sound: WhiteNoiseSound) -> Float {
        let value: Float
        switch sound {
        case .rain:
            value = rainSample()
        case .ocean:
            value = oceanSample()
        case .fan:
            value = fanSample()
        case .pink:
            value = pinkSample()
        case .dryer:
            value = dryerSample()
        case .cabin:
            value = cabinSample()
        case .shush:
            value = shushSample()
        }

        return max(-0.85, min(0.85, value))
    }

    private mutating func rainSample() -> Float {
        let noise = whiteSample()
        let softDrop = whiteSample() * whiteSample() * 0.12
        return noise * 0.42 + softDrop
    }

    private mutating func oceanSample() -> Float {
        wavePhase += 1.0 / sampleRate
        if wavePhase > 1 {
            wavePhase -= 1
        }

        let swell = Float((sin(wavePhase * Double.pi * 2.0 * 0.12) + 1.0) * 0.5)
        brownValue = brownValue * 0.995 + whiteSample() * 0.018
        return brownValue * (0.45 + swell * 0.65)
    }

    private mutating func fanSample() -> Float {
        fanPhase += 96.0 / sampleRate
        if fanPhase > 1 {
            fanPhase -= 1
        }

        let hum = Float(sin(fanPhase * Double.pi * 2.0)) * 0.18
        brownValue = brownValue * 0.985 + whiteSample() * 0.025
        return hum + brownValue * 0.72
    }

    private mutating func pinkSample() -> Float {
        pinkCounter &+= 1
        var counter = pinkCounter
        var index = 0
        while counter & 1 == 0 && index < pinkRows.count {
            pinkRows[index] = whiteSample()
            counter >>= 1
            index += 1
        }

        let sum = pinkRows.reduce(Float(0), +) + whiteSample()
        return sum / Float(pinkRows.count + 1)
    }

    private mutating func dryerSample() -> Float {
        dryerPhase += 118.0 / sampleRate
        if dryerPhase > 1 {
            dryerPhase -= 1
        }

        let hum = Float(sin(dryerPhase * Double.pi * 2.0)) * 0.17
            + Float(sin(dryerPhase * Double.pi * 4.0)) * 0.06
        brownValue = brownValue * 0.972 + whiteSample() * 0.052
        return hum + brownValue * 0.82 + whiteSample() * 0.20
    }

    private mutating func cabinSample() -> Float {
        cabinPhase += 62.0 / sampleRate
        if cabinPhase > 1 {
            cabinPhase -= 1
        }

        wavePhase += 0.07 / sampleRate
        if wavePhase > 1 {
            wavePhase -= 1
        }

        let engineHum = Float(sin(cabinPhase * Double.pi * 2.0)) * 0.18
            + Float(sin(cabinPhase * Double.pi * 4.0)) * 0.08
            + Float(sin(cabinPhase * Double.pi)) * 0.05
        let pressure = Float((sin(wavePhase * Double.pi * 2.0) + 1.0) * 0.5)
        brownValue = brownValue * 0.992 + whiteSample() * 0.014
        return brownValue * (0.88 + pressure * 0.18) + engineHum
    }

    private mutating func shushSample() -> Float {
        shushPhase += 0.075 / sampleRate
        if shushPhase > 1 {
            shushPhase -= 1
        }

        let rawNoise = whiteSample()
        let airyNoise = rawNoise - previousShushNoise * 0.58
        previousShushNoise = rawNoise

        let mouth = Self.bandPassSample(
            airyNoise,
            sampleRate: sampleRate,
            cutoff: 2_450,
            damping: 0.58,
            low: &shushMouthLow,
            band: &shushMouthBand
        )
        let softAir = Self.bandPassSample(
            airyNoise,
            sampleRate: sampleRate,
            cutoff: 4_250,
            damping: 0.82,
            low: &shushAirLow,
            band: &shushAirBand
        )

        shushWarmth = shushWarmth * 0.994 + pinkSample() * 0.006
        let breath = Float((sin(shushPhase * Double.pi * 2.0) + 1.0) * 0.5)
        let tinyFlutter = Float(sin(shushPhase * Double.pi * 2.0 * 19.0)) * 0.025
        let envelope = 0.68 + breath * 0.19 + tinyFlutter
        let shapedAir = mouth * 0.72 + softAir * 0.28 + shushWarmth * 0.055

        shushSmoothed = shushSmoothed * 0.64 + shapedAir * 0.36
        return shushSmoothed * envelope * 0.72
    }

    private mutating func whiteSample() -> Float {
        randomState = randomState &* 6364136223846793005 &+ 1442695040888963407
        let value = UInt32(truncatingIfNeeded: randomState >> 32)
        return Float(value) / Float(UInt32.max) * 2 - 1
    }

    private static func bandPassSample(
        _ input: Float,
        sampleRate: Double,
        cutoff: Float,
        damping: Float,
        low: inout Float,
        band: inout Float
    ) -> Float {
        let frequency = min(0.98, Float(2.0 * sin(Double.pi * Double(cutoff) / sampleRate)))
        low += frequency * band
        let high = input - low - damping * band
        band += frequency * high
        return band
    }
}
