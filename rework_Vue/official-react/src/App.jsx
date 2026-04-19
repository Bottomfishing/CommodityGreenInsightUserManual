import { BackgroundGradientAnimation } from "@/components/ui/background-gradient-animation";
import { Button } from "@/components/ui/button";
import { CanvasText } from "@/components/ui/canvas-text";
import { CardBody, CardContainer, CardItem } from "@/components/ui/3d-card";
import { NoiseBackground } from "@/components/ui/noise-background";

const TREE_IMAGE =
  "/@fs/C:/Users/12725/.cursor/projects/c-Users-12725-Desktop/assets/c__Users_12725_AppData_Roaming_Cursor_User_workspaceStorage_2f5f32168527502832b6556507273f18_images_image-3947fcec-9787-43b2-9d9e-7f2d7e3e3daf.png";
const OIL_PRICE_IMAGE =
  "/@fs/C:/Users/12725/.cursor/projects/c-Users-12725-Desktop/assets/c__Users_12725_AppData_Roaming_Cursor_User_workspaceStorage_2f5f32168527502832b6556507273f18_images_image-db3c75b9-c37b-48e1-b5fe-b2632155d15c.png";
const NEW_ENERGY_IMAGE =
  "/@fs/C:/Users/12725/.cursor/projects/c-Users-12725-Desktop/assets/c__Users_12725_AppData_Roaming_Cursor_User_workspaceStorage_2f5f32168527502832b6556507273f18_images_image-1e4997d4-c659-48c1-bc2a-e530919131a9.png";

function App() {
  return (
    <main className="relative min-h-screen w-full overflow-hidden">
      <BackgroundGradientAnimation
        containerClassName="absolute inset-0 h-screen w-full"
        className="absolute inset-0"
        interactive={true}
      />

      <section className="relative z-20 min-h-screen px-6">
        <div className="absolute left-20 top-20 md:left-32 md:top-24">
          <CanvasText
            text="大宗绿测"
            className="text-6xl md:text-8xl font-extrabold tracking-tight drop-shadow-[0_2px_10px_rgba(0,0,0,0.45)]"
            backgroundClassName="bg-emerald-700"
            colors={["#bbf7d0", "#86efac", "#4ade80", "#34d399", "#22c55e", "#16a34a", "#15803d"]}
            lineGap={10}
            lineWidth={1.8}
            curveIntensity={230}
            animationDuration={5}
          />
          <p className="absolute left-[70%] top-[130%] w-max text-2xl md:text-4xl font-bold tracking-tight text-white drop-shadow-[0_6px_18px_rgba(0,0,0,0.85)]">
            - 基于机器学习的油价预测与绿色金融平台
          </p>
        </div>

        <div className="absolute left-1/2 top-[40%] -translate-x-1/2 md:top-[42%] flex items-start gap-8">
          <CardContainer containerClassName="!py-0">
            <CardBody className="h-[300px] w-[420px] rounded-3xl border border-white/20 bg-white/10 backdrop-blur-md p-4">
              <CardItem
                translateZ={50}
                className="text-center text-xl font-semibold tracking-wide text-white drop-shadow-[0_2px_10px_rgba(0,0,0,0.45)]"
              >
                油价金融可视化
              </CardItem>
              <CardItem
                as="p"
                translateZ={65}
                className="mt-1 text-center text-sm text-white/75"
              >
                Oil Price Finance Visualization
              </CardItem>
              <CardItem translateZ={90} className="mt-3">
                <img
                  src={OIL_PRICE_IMAGE}
                  alt="oil-price"
                  className="h-[210px] w-full rounded-2xl object-cover"
                />
              </CardItem>
            </CardBody>
          </CardContainer>

          <CardContainer containerClassName="!py-0">
            <CardBody className="h-[300px] w-[420px] rounded-3xl border border-white/20 bg-white/10 backdrop-blur-md p-4">
              <CardItem
                translateZ={50}
                className="text-center text-xl font-semibold tracking-wide text-white drop-shadow-[0_2px_10px_rgba(0,0,0,0.45)]"
              >
                绿色债券金融可视化
              </CardItem>
              <CardItem
                as="p"
                translateZ={65}
                className="mt-1 text-center text-sm text-white/75"
              >
                Green Bond Finance Visualization
              </CardItem>
              <CardItem translateZ={90} className="mt-3">
                <img
                  src={TREE_IMAGE}
                  alt="tree"
                  className="h-[210px] w-full rounded-2xl object-cover"
                />
              </CardItem>
            </CardBody>
          </CardContainer>

          <CardContainer containerClassName="!py-0">
            <CardBody className="h-[300px] w-[420px] rounded-3xl border border-white/20 bg-white/10 backdrop-blur-md p-4">
              <CardItem
                translateZ={50}
                className="text-center text-xl font-semibold tracking-wide text-white drop-shadow-[0_2px_10px_rgba(0,0,0,0.45)]"
              >
                新能源金融可视化
              </CardItem>
              <CardItem
                as="p"
                translateZ={65}
                className="mt-1 text-center text-sm text-white/75"
              >
                New Energy Finance Visualization
              </CardItem>
              <CardItem translateZ={90} className="mt-3">
                <img
                  src={NEW_ENERGY_IMAGE}
                  alt="new-energy"
                  className="h-[210px] w-full rounded-2xl object-cover"
                />
              </CardItem>
            </CardBody>
          </CardContainer>
        </div>

        <div className="absolute bottom-20 left-1/2 -translate-x-1/2 flex items-center justify-center gap-20 flex-wrap">
          <NoiseBackground
            containerClassName="rounded-[26px] p-[3px] min-w-[270px] bg-transparent shadow-none"
            className="rounded-[24px]"
            gradientColors={["rgb(56, 189, 248)", "rgb(147, 197, 253)", "rgb(196, 181, 253)"]}
            noiseIntensity={0.12}
            speed={0.18}
            animating={true}
          >
            <Button className="w-full rounded-[22px] border border-white/55 bg-transparent text-white hover:bg-white/10 shadow-none px-6 py-4 text-xl font-normal tracking-normal">
              立即开始 →
            </Button>
          </NoiseBackground>

          <NoiseBackground
            containerClassName="rounded-[26px] p-[3px] min-w-[270px] bg-transparent shadow-none"
            className="rounded-[24px]"
            gradientColors={["rgb(56, 189, 248)", "rgb(147, 197, 253)", "rgb(196, 181, 253)"]}
            noiseIntensity={0.12}
            speed={0.18}
            animating={true}
          >
            <Button variant="outline" className="w-full rounded-[22px] border border-white/55 bg-transparent text-white hover:bg-white/10 shadow-none px-6 py-4 text-xl font-normal tracking-normal" asChild>
              <a href="/大宗绿测用户手册.pdf" target="_blank" rel="noreferrer">
                用户手册 →
              </a>
            </Button>
          </NoiseBackground>
        </div>
      </section>
    </main>
  );
}

export default App;
