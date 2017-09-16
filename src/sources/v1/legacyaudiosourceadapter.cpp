#include "sources/v1/legacyaudiosourceadapter.h"

#include "sources/audiosource.h"

#include "util/logger.h"


namespace mixxx {

namespace {

const Logger kLogger("LegacyAudioSourceAdapter");

} // anonymous namespace

LegacyAudioSourceAdapter::LegacyAudioSourceAdapter(
        AudioSource* pOwner,
        LegacyAudioSource* pImpl)
    : m_pOwner(pOwner),
      m_pImpl(pImpl) {
}

ReadableSampleFrames LegacyAudioSourceAdapter::readSampleFramesClamped(
        ReadMode readMode,
        WritableSampleFrames writableSampleFrames) {

    const SINT firstFrameIndex = writableSampleFrames.frameIndexRange().start();

    const SINT seekFrameIndex = m_pImpl->seekSampleFrame(firstFrameIndex);
    if (seekFrameIndex < firstFrameIndex) {
        const auto precedingFrames =
                IndexRange::between(seekFrameIndex, firstFrameIndex);
        kLogger.info()
                << "Skipping preceding frames"
                << precedingFrames;
        if (precedingFrames.length() != m_pImpl->readSampleFrames(precedingFrames.length(), nullptr)) {
            kLogger.warning()
                    << "Failed to skip preceding frames"
                    << precedingFrames;
            return ReadableSampleFrames();
        }
    }
    DEBUG_ASSERT(seekFrameIndex >= firstFrameIndex);

    if (seekFrameIndex > firstFrameIndex) {
        const SINT unreadableFrameOffset = seekFrameIndex - firstFrameIndex;
        kLogger.warning()
                << "Dropping"
                << unreadableFrameOffset
                << "unreadable frames";
        if (writableSampleFrames.frameIndexRange().containsIndex(seekFrameIndex)) {
            const auto remainingFrameIndexRange =
                    IndexRange::between(seekFrameIndex, writableSampleFrames.frameIndexRange().end());
            if (readMode != ReadMode::Skip) {
                writableSampleFrames = WritableSampleFrames(
                        remainingFrameIndexRange,
                        SampleBuffer::WritableSlice(
                                writableSampleFrames.sampleBuffer().data(m_pOwner->frames2samples(unreadableFrameOffset)),
                                m_pOwner->frames2samples(remainingFrameIndexRange.length())));
            } else {
                writableSampleFrames = WritableSampleFrames(remainingFrameIndexRange);
            }
        } else {
            writableSampleFrames = WritableSampleFrames();
        }
    }
    // Read or skip data
    const SINT numFramesRead =
            m_pImpl->readSampleFrames(
                    writableSampleFrames.frameIndexRange().length(),
                    (readMode != ReadMode::Skip) ? writableSampleFrames.sampleBuffer().data() : nullptr);
    const auto resultFrameIndexRange =
            IndexRange::forward(writableSampleFrames.frameIndexRange().start(), numFramesRead);
    if (readMode == ReadMode::Skip) {
        return ReadableSampleFrames(resultFrameIndexRange);
    } else {
        return ReadableSampleFrames(
                resultFrameIndexRange,
                SampleBuffer::ReadableSlice(
                        writableSampleFrames.sampleBuffer().data(),
                        m_pOwner->frames2samples(resultFrameIndexRange.length())));
    }
}

} // namespace mixxx
